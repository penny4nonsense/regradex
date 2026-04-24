"""
test_grader.py
--------------
Unit tests for regradex.grader.

All tests are self-contained — no external files or data dependencies.
Fixtures use simple, readable patterns so the tests are easy to reason
about independently of any real exam content.
"""

import re
import pytest
from regradex.grader import (
    CompiledQuestion,
    compile_question,
    match_regexes,
    evaluate_logic,
    evaluate,
    evaluate_with_status,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def simple_config():
    """A minimal question config dict with two patterns and simple logic.

    Pattern 0: matches a number (e.g. '42')
    Pattern 1: matches a unit word 'dollars' case-insensitively

    Logic:
        - Both match -> 10 points
        - Number only -> 5 points
    """
    return {
        'question': 'What is the answer?',
        'answer': '42 dollars',
        'regex': [r'\d+', r'[Dd][Oo][Ll][Ll][Aa][Rr][Ss]'],
        'logic': [
            {'all': [0, 1], 'score': 10},
            {'any': [0], 'score': 5},
        ]
    }


@pytest.fixture
def compiled(simple_config):
    """A CompiledQuestion built from simple_config."""
    return compile_question(simple_config)


@pytest.fixture
def zero_score_config():
    """A config where a matched rule scores 0.

    Used to verify that evaluate_with_status distinguishes a recognized
    wrong answer (matched, score=0) from no match (unmatched, score=0).

    Pattern 0: matches 'wrong'
    Logic:
        - 'wrong' matched -> recognized but scores 0
    """
    return {
        'question': 'What is the answer?',
        'answer': '42 dollars',
        'regex': [r'wrong'],
        'logic': [
            {'any': [0], 'score': 0},
        ]
    }


# ---------------------------------------------------------------------------
# compile_question
# ---------------------------------------------------------------------------

class TestCompileQuestion:

    def test_returns_compiled_question(self, simple_config):
        result = compile_question(simple_config)
        assert isinstance(result, CompiledQuestion)

    def test_patterns_are_compiled(self, simple_config):
        result = compile_question(simple_config)
        assert all(isinstance(p, re.Pattern) for p in result.patterns)

    def test_pattern_count_matches_regex_list(self, simple_config):
        result = compile_question(simple_config)
        assert len(result.patterns) == len(simple_config['regex'])

    def test_question_and_answer_preserved(self, simple_config):
        result = compile_question(simple_config)
        assert result.question == simple_config['question']
        assert result.answer == simple_config['answer']

    def test_logic_preserved(self, simple_config):
        result = compile_question(simple_config)
        assert result.logic == simple_config['logic']


# ---------------------------------------------------------------------------
# match_regexes
# ---------------------------------------------------------------------------

class TestMatchRegexes:

    def test_all_patterns_match(self, compiled):
        result = match_regexes('42 dollars', compiled.patterns)
        assert result == [True, True]

    def test_partial_match(self, compiled):
        result = match_regexes('42', compiled.patterns)
        assert result == [True, False]

    def test_no_patterns_match(self, compiled):
        result = match_regexes('no answer here', compiled.patterns)
        assert result == [False, False]

    def test_empty_string(self, compiled):
        result = match_regexes('', compiled.patterns)
        assert result == [False, False]

    def test_returns_list_of_bools(self, compiled):
        result = match_regexes('42 dollars', compiled.patterns)
        assert isinstance(result, list)
        assert all(isinstance(v, bool) for v in result)


# ---------------------------------------------------------------------------
# evaluate_logic
# ---------------------------------------------------------------------------

class TestEvaluateLogic:

    def test_all_rule_fires(self, compiled):
        result = evaluate_logic([True, True], compiled.logic)
        assert result == 10

    def test_any_rule_fires(self, compiled):
        result = evaluate_logic([True, False], compiled.logic)
        assert result == 5

    def test_no_rule_matches_returns_zero(self, compiled):
        result = evaluate_logic([False, False], compiled.logic)
        assert result == 0

    def test_first_matching_rule_wins(self):
        """First rule should win even if a later rule would also match."""
        logic = [
            {'any': [0], 'score': 10},
            {'any': [0], 'score': 5},
        ]
        result = evaluate_logic([True, False], logic)
        assert result == 10

    def test_matched_rule_can_score_zero(self):
        """A rule that matches but scores 0 is valid — not the same as no match."""
        logic = [{'any': [0], 'score': 0}]
        result = evaluate_logic([True], logic)
        assert result == 0


# ---------------------------------------------------------------------------
# evaluate
# ---------------------------------------------------------------------------

class TestEvaluate:

    def test_full_credit(self, compiled):
        assert evaluate('42 dollars', compiled) == 10

    def test_partial_credit(self, compiled):
        assert evaluate('42', compiled) == 5

    def test_no_credit(self, compiled):
        assert evaluate('no answer here', compiled) == 0

    def test_empty_answer(self, compiled):
        assert evaluate('', compiled) == 0


# ---------------------------------------------------------------------------
# evaluate_with_status
# ---------------------------------------------------------------------------

class TestEvaluateWithStatus:

    def test_full_credit_matched(self, compiled):
        score, matched = evaluate_with_status('42 dollars', compiled)
        assert score == 10
        assert matched is True

    def test_partial_credit_matched(self, compiled):
        score, matched = evaluate_with_status('42', compiled)
        assert score == 5
        assert matched is True

    def test_no_match_returns_false(self, compiled):
        score, matched = evaluate_with_status('no answer here', compiled)
        assert score == 0
        assert matched is False

    def test_zero_score_match_returns_true(self, zero_score_config):
        """A matched rule scoring 0 should return matched=True, not False."""
        compiled_zero = compile_question(zero_score_config)
        score, matched = evaluate_with_status('wrong answer', compiled_zero)
        assert score == 0
        assert matched is True

    def test_no_match_distinguished_from_zero_score_match(self, zero_score_config):
        """The critical distinction: unrecognized answer vs recognized wrong answer."""
        compiled_zero = compile_question(zero_score_config)
        _, matched_wrong = evaluate_with_status('wrong answer', compiled_zero)
        _, matched_unrecognized = evaluate_with_status('something else entirely', compiled_zero)
        assert matched_wrong is True
        assert matched_unrecognized is False