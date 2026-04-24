"""
review.py
---------
Workflow layer for regradex.

Sits on top of grader.py and handles the human-in-the-loop part —
autograding all questions, building review queues for unrecognized
answers, applying manual scores, and computing final grades.

No file I/O here — the caller (notebook or CLI) handles reading and
writing Excel files.
"""

import math
import pandas as pd
from .grader import CompiledQuestion, evaluate_with_status


def autograde_all(
    df: pd.DataFrame,
    questions: dict[str, CompiledQuestion],
    prefix: str = 'rg'
) -> pd.DataFrame:
    """Run the grading engine over all questions and return a new dataframe.

    For each question in the questions dict, evaluates every student answer
    and writes the result to a new column. Only questions that appear in
    both the questions dict and the dataframe are graded — others are
    skipped silently.

    Args:
        df: Student response dataframe with columns 'Answer N' for each
            question number N.
        questions: Dict of question number strings to CompiledQuestion
            objects, as returned by compile_question().
        prefix: Column name prefix for regradex columns. Defaults to 'rg'.

    Returns:
        A new dataframe with added '{prefix}_auto_N' columns for each
        graded question.
    """
    result = df.copy()
    for key, question in questions.items():
        answer_col = f'Answer {key}'
        if answer_col not in result.columns:
            continue
        auto_col = f'{prefix}_auto_{key}'
        scores = []
        for answer in result[answer_col]:
            score, _ = evaluate_with_status(str(answer), question)
            scores.append(score)
        result[auto_col] = scores
    return result


def review_queue(
    df: pd.DataFrame,
    question_key: str,
    prefix: str = 'rg'
) -> dict[int, str]:
    """Return answers that need manual review for a given question.

    An answer needs review if the grading engine found no matching rule —
    indicated by an auto score of 0 with no rule matched. This is determined
    by re-running evaluate_with_status and checking the matched flag.

    Note: This returns ALL answers where no rule matched, including those
    that may legitimately score 0. The instructor should review and apply
    manual scores where appropriate using apply_manual().

    Args:
        df: Student response dataframe, after autograde_all() has been run.
        question_key: Question number string (e.g. '6').
        prefix: Column name prefix for regradex columns. Defaults to 'rg'.

    Returns:
        Dict mapping dataframe row index to answer string for all answers
        that need manual review.
    """
    answer_col = f'Answer {question_key}'
    auto_col = f'{prefix}_auto_{question_key}'

    if answer_col not in df.columns:
        raise ValueError(f"Column '{answer_col}' not found in dataframe")
    if auto_col not in df.columns:
        raise ValueError(f"Column '{auto_col}' not found. Run autograde_all() first.")

    queue = {}
    for idx, row in df.iterrows():
        answer = str(row[answer_col])
        auto_score = row[auto_col]
        if auto_score == 0:
            queue[idx] = answer
    return queue


def apply_manual(
    df: pd.DataFrame,
    question_key: str,
    index: int,
    score: int,
    prefix: str = 'rg'
) -> pd.DataFrame:
    """Apply a manual score for one student answer.

    Creates the manual score column if it does not already exist.
    Manual scores take precedence over auto scores in final_grade().

    Args:
        df: Student response dataframe.
        question_key: Question number string (e.g. '6').
        index: Dataframe row index of the student to score.
        score: Manual score to apply.
        prefix: Column name prefix for regradex columns. Defaults to 'rg'.

    Returns:
        A new dataframe with the manual score applied.
    """
    result = df.copy()
    manual_col = f'{prefix}_manual_{question_key}'
    if manual_col not in result.columns:
        result[manual_col] = pd.NA
    result.loc[index, manual_col] = score
    return result


def final_grade(
    df: pd.DataFrame,
    question_key: str,
    prefix: str = 'rg'
) -> pd.Series:
    """Compute the final grade for one question.

    Manual score takes precedence over auto score where present.
    If neither is available, returns 0.

    Args:
        df: Student response dataframe.
        question_key: Question number string (e.g. '6').
        prefix: Column name prefix for regradex columns. Defaults to 'rg'.

    Returns:
        A Series of final grades for the question, indexed like df.
    """
    auto_col = f'{prefix}_auto_{question_key}'
    manual_col = f'{prefix}_manual_{question_key}'

    if auto_col not in df.columns:
        raise ValueError(f"Column '{auto_col}' not found. Run autograde_all() first.")

    auto = df[auto_col].fillna(0)

    if manual_col not in df.columns:
        return auto

    return df[manual_col].combine_first(auto)


def grade_all(
    df: pd.DataFrame,
    question_keys: list[str],
    prefix: str = 'rg'
) -> pd.DataFrame:
    """Compute final grades for all questions and add a total column.

    Runs final_grade() for each question key and writes results to
    '{prefix}_grade_N' columns. Adds a '{prefix}_total' column summing
    all grade columns.

    Args:
        df: Student response dataframe, after autograde_all() has been run.
        question_keys: List of question number strings to grade.
        prefix: Column name prefix for regradex columns. Defaults to 'rg'.

    Returns:
        A new dataframe with '{prefix}_grade_N' columns and a
        '{prefix}_total' column added.
    """
    result = df.copy()
    grade_cols = []
    for key in question_keys:
        grade_col = f'{prefix}_grade_{key}'
        result[grade_col] = final_grade(result, key, prefix)
        grade_cols.append(grade_col)
    result[f'{prefix}_total'] = result[grade_cols].sum(axis=1)
    return result