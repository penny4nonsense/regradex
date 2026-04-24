"""
grader.py
---------
Core grading engine for regradex.

This module is pure logic — no I/O, no pandas, no side effects.
It takes a compiled question config and a student answer string,
and returns a score.

A score of 0 with no matching rule indicates the answer should be
queued for manual review.
"""

import re
from dataclasses import dataclass


@dataclass
class CompiledQuestion:
    """A question config with regex patterns compiled and ready for matching.

    Attributes:
        question: The question text as shown to students.
        answer: The canonical correct answer.
        patterns: Compiled regex patterns. Each pattern corresponds to one
            matching criterion. The boolean match vector passed to
            evaluate_logic is indexed the same way as this list.
        logic: Ordered list of scoring rules. Each rule has an 'all' or 'any'
            key containing a list of pattern indices, and a 'score' key. Rules
            are evaluated in order and the first match wins. A score of 0 from
            a matched rule is valid — it means the answer was recognized but
            earns no credit. A score of 0 from no match means manual review
            is needed.
    """
    question: str
    answer: str
    patterns: list[re.Pattern]
    logic: list[dict]


def compile_question(question_config: dict) -> CompiledQuestion:
    """Compile a raw question config dict into a CompiledQuestion.

    Compiles all regex strings into re.Pattern objects. Does not validate
    the config structure — call schema.validate() before this if needed.

    Args:
        question_config: A single question entry from answers.json, with keys
            'question', 'answer', 'regex', and 'logic'.

    Returns:
        A ready-to-use CompiledQuestion.
    """
    patterns = [re.compile(pattern) for pattern in question_config['regex']]
    return CompiledQuestion(
        question=question_config['question'],
        answer=question_config['answer'],
        patterns=patterns,
        logic=question_config['logic']
    )


def match_regexes(answer: str, patterns: list[re.Pattern]) -> list[bool]:
    """Run all patterns against an answer string.

    Args:
        answer: The student's answer.
        patterns: Compiled regex patterns from a CompiledQuestion.

    Returns:
        Boolean match vector where match_vector[i] is True if patterns[i]
        matched the answer.
    """
    return [pattern.search(str(answer)) is not None for pattern in patterns]


def evaluate_logic(match_vector: list[bool], logic: list[dict]) -> int:
    """Walk logic rules in order and return the score for the first match.

    Rules are evaluated in priority order — highest score rules should come
    first in the logic list. Short-circuits on the first matching rule.

    A rule matches if:
        - It has an 'all' key and all listed pattern indices are True, or
        - It has an 'any' key and at least one listed pattern index is True.

    If no rule matches, returns 0. This signals that the answer should be
    queued for manual review.

    Args:
        match_vector: Boolean match vector from match_regexes.
        logic: Ordered list of scoring rules, each with 'all' or 'any'
            and 'score'.

    Returns:
        Score for the answer. 0 either means no credit or no match —
        use evaluate_with_status() to distinguish these cases.
    """
    for rule in logic:
        if 'all' in rule and all(match_vector[i] for i in rule['all']):
            return rule['score']
        if 'any' in rule and any(match_vector[i] for i in rule['any']):
            return rule['score']
    return 0


def evaluate(answer: str, question: CompiledQuestion) -> int:
    """Score a single student answer against a compiled question.

    Combines match_regexes and evaluate_logic into a single call. A return
    value of 0 may mean no credit or may mean no rule matched and the answer
    needs manual review — use evaluate_with_status() if you need to
    distinguish these cases.

    Args:
        answer: The student's answer.
        question: The compiled question config.

    Returns:
        Score for the answer.
    """
    match_vector = match_regexes(answer, question.patterns)
    return evaluate_logic(match_vector, question.logic)


def evaluate_with_status(answer: str, question: CompiledQuestion) -> tuple[int, bool]:
    """Score a student answer and indicate whether a rule was matched.

    Use this instead of evaluate() when you need to distinguish between a
    matched rule that scores 0 (wrong but recognized) and no match at all
    (needs manual review).

    Args:
        answer: The student's answer.
        question: The compiled question config.

    Returns:
        A tuple of (score, matched) where matched is True if any logic rule
        fired, and False if no rule matched and manual review is needed.
    """
    match_vector = match_regexes(answer, question.patterns)
    for rule in question.logic:
        if 'all' in rule and all(match_vector[i] for i in rule['all']):
            return rule['score'], True
        if 'any' in rule and any(match_vector[i] for i in rule['any']):
            return rule['score'], True
    return 0, False