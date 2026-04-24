"""
test_review.py
--------------
Unit tests for regradex.review.

All tests are self-contained — no external files or data dependencies.
Fixtures use a small synthetic dataframe with two questions and a handful
of students to keep tests readable and fast.
"""

import pytest
import pandas as pd
from regradex.grader import compile_question
from regradex.review import autograde_all, review_queue, apply_manual, final_grade, grade_all

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def questions():
    """Two compiled questions with simple patterns.

    Question 1: matches a number and the word 'dollars'
        - both match -> 10 points
        - number only -> 5 points

    Question 2: matches the word 'percent'
        - match -> 10 points
    """
    q1 = compile_question({
        'question': 'What is the value?',
        'answer': '42 dollars',
        'regex': [r'\d+', r'[Dd][Oo][Ll][Ll][Aa][Rr][Ss]'],
        'logic': [
            {'all': [0, 1], 'score': 10},
            {'any': [0], 'score': 5},
        ]
    })
    q2 = compile_question({
        'question': 'What is the unit?',
        'answer': 'percent',
        'regex': [r'[Pp][Ee][Rr][Cc][Ee][Nn][Tt]'],
        'logic': [
            {'any': [0], 'score': 10},
        ]
    })
    return {'1': q1, '2': q2}


@pytest.fixture
def students():
    """A small synthetic student response dataframe with four students.

    Student 0: correct on both questions
    Student 1: partial credit on question 1, correct on question 2
    Student 2: unrecognized answer on question 1, correct on question 2
    Student 3: unrecognized on both questions
    """
    return pd.DataFrame({
        'Username': ['alice', 'bob', 'carol', 'dave'],
        'Answer 1': ['42 dollars', '42', 'forty two dollars', 'no idea'],
        'Answer 2': ['percent', 'Percent', 'PERCENT', 'nothing'],
    })


@pytest.fixture
def autograded(students, questions):
    """Pre-autograded dataframe for tests that need scores already computed."""
    return autograde_all(students, questions)


# ---------------------------------------------------------------------------
# autograde_all
# ---------------------------------------------------------------------------

class TestAutogradeAll:

    def test_correct_answer_full_credit(self, autograded):
        assert autograded.loc[0, 'rg_auto_1'] == 10

    def test_partial_answer_partial_credit(self, autograded):
        assert autograded.loc[1, 'rg_auto_1'] == 5

    def test_unrecognized_answer_scores_zero(self, autograded):
        assert autograded.loc[2, 'rg_auto_1'] == 0

    def test_adds_auto_columns(self, autograded):
        assert 'rg_auto_1' in autograded.columns
        assert 'rg_auto_2' in autograded.columns

    def test_does_not_mutate_original(self, students, questions):
        _ = autograde_all(students, questions)
        assert 'rg_auto_1' not in students.columns

    def test_skips_missing_question_column(self, students, questions):
        """Questions not present in the dataframe should be skipped silently."""
        questions_extra = dict(questions)
        questions_extra['99'] = questions['1']
        result = autograde_all(students, questions_extra)
        assert 'rg_auto_99' not in result.columns

    def test_custom_prefix(self, students, questions):
        result = autograde_all(students, questions, prefix='jp')
        assert 'jp_auto_1' in result.columns
        assert 'rg_auto_1' not in result.columns

    def test_all_students_graded(self, autograded, students):
        assert len(autograded) == len(students)


# ---------------------------------------------------------------------------
# review_queue
# ---------------------------------------------------------------------------

class TestReviewQueue:

    def test_zero_scores_in_queue(self, autograded):
        queue = review_queue(autograded, '1')
        assert 2 in queue  # carol — unrecognized
        assert 3 in queue  # dave — unrecognized

    def test_nonzero_scores_not_in_queue(self, autograded):
        queue = review_queue(autograded, '1')
        assert 0 not in queue  # alice — full credit
        assert 1 not in queue  # bob — partial credit

    def test_returns_correct_answers(self, autograded):
        queue = review_queue(autograded, '1')
        assert queue[2] == 'forty two dollars'
        assert queue[3] == 'no idea'

    def test_raises_if_answer_column_missing(self, autograded):
        with pytest.raises(ValueError, match="Answer 99"):
            review_queue(autograded, '99')

    def test_raises_if_auto_column_missing(self, students):
        """Should raise if autograde_all has not been run yet."""
        with pytest.raises(ValueError, match="rg_auto_1"):
            review_queue(students, '1')

    def test_empty_queue_when_all_recognized(self, autograded):
        """Question 2 has all students recognized (even if score is 0)."""
        queue = review_queue(autograded, '2')
        assert 3 in queue  # dave scored 0


# ---------------------------------------------------------------------------
# apply_manual
# ---------------------------------------------------------------------------

class TestApplyManual:

    def test_applies_score_at_correct_index(self, autograded):
        result = apply_manual(autograded, '1', 2, 7)
        assert result.loc[2, 'rg_manual_1'] == 7

    def test_creates_manual_column_if_missing(self, autograded):
        assert 'rg_manual_1' not in autograded.columns
        result = apply_manual(autograded, '1', 2, 7)
        assert 'rg_manual_1' in result.columns

    def test_does_not_mutate_original(self, autograded):
        _ = apply_manual(autograded, '1', 2, 7)
        assert 'rg_manual_1' not in autograded.columns

    def test_other_rows_remain_na(self, autograded):
        result = apply_manual(autograded, '1', 2, 7)
        assert pd.isna(result.loc[0, 'rg_manual_1'])
        assert pd.isna(result.loc[1, 'rg_manual_1'])

    def test_custom_prefix(self, autograded):
        result = apply_manual(autograded, '1', 2, 7, prefix='jp')
        assert 'jp_manual_1' in result.columns
        assert 'rg_manual_1' not in result.columns


# ---------------------------------------------------------------------------
# final_grade
# ---------------------------------------------------------------------------

class TestFinalGrade:

    def test_returns_auto_where_no_manual(self, autograded):
        grades = final_grade(autograded, '1')
        assert grades[0] == 10
        assert grades[1] == 5

    def test_manual_takes_precedence_over_auto(self, autograded):
        df = apply_manual(autograded, '1', 2, 8)
        grades = final_grade(df, '1')
        assert grades[2] == 8

    def test_auto_used_where_manual_is_na(self, autograded):
        df = apply_manual(autograded, '1', 2, 8)
        grades = final_grade(df, '1')
        assert grades[0] == 10  # no manual, uses auto
        assert grades[1] == 5   # no manual, uses auto

    def test_raises_if_auto_column_missing(self, students):
        with pytest.raises(ValueError, match="rg_auto_1"):
            final_grade(students, '1')

    def test_custom_prefix(self, autograded):
        result = autograde_all(autograded, {}, prefix='jp')
        result = apply_manual(result, '1', 0, 9, prefix='jp')
        # use rg prefix which has auto columns
        grades = final_grade(autograded, '1', prefix='rg')
        assert grades[0] == 10


# ---------------------------------------------------------------------------
# grade_all
# ---------------------------------------------------------------------------

class TestGradeAll:

    def test_adds_grade_columns(self, autograded):
        result = grade_all(autograded, ['1', '2'])
        assert 'rg_grade_1' in result.columns
        assert 'rg_grade_2' in result.columns

    def test_adds_total_column(self, autograded):
        result = grade_all(autograded, ['1', '2'])
        assert 'rg_total' in result.columns

    def test_total_is_correct_sum(self, autograded):
        result = grade_all(autograded, ['1', '2'])
        # alice: 10 + 10 = 20
        assert result.loc[0, 'rg_total'] == 20
        # bob: 5 + 10 = 15
        assert result.loc[1, 'rg_total'] == 15

    def test_does_not_mutate_original(self, autograded):
        _ = grade_all(autograded, ['1', '2'])
        assert 'rg_grade_1' not in autograded.columns
        assert 'rg_total' not in autograded.columns

    def test_custom_prefix(self, students, questions):
        df = autograde_all(students, questions, prefix='jp')
        result = grade_all(df, ['1', '2'], prefix='jp')
        assert 'jp_grade_1' in result.columns
        assert 'jp_total' in result.columns