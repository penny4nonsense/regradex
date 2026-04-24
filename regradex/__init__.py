"""
regradex
--------
A regex-based autograder for short-answer quantitative exams,
with tiered partial credit and a manual review queue for incorrect responses.
"""

from .grader import (
    CompiledQuestion,
    compile_question,
    match_regexes,
    evaluate_logic,
    evaluate,
    evaluate_with_status,
)

from .schema import (
    validate,
    validate_all,
)

from .review import (
    autograde_all,
    review_queue,
    apply_manual,
    final_grade,
    grade_all,
)

__all__ = [
    # grader
    'CompiledQuestion',
    'compile_question',
    'match_regexes',
    'evaluate_logic',
    'evaluate',
    'evaluate_with_status',
    # schema
    'validate',
    'validate_all',
    # review
    'autograde_all',
    'review_queue',
    'apply_manual',
    'final_grade',
    'grade_all',
]

__version__ = '0.1.0'