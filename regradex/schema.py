"""
schema.py
---------
Validation for regradex question config dicts.

Call validate() before compile_question() to catch malformed configs
early with descriptive error messages.
"""

import re


REQUIRED_KEYS = {'question', 'answer'}


def _validate_structure(config: dict) -> None:
    """Check that all required top-level keys are present and the right type.

    Args:
        config: A single question config dict.

    Raises:
        ValueError: If any required key is missing or the wrong type.
    """
    missing = REQUIRED_KEYS - config.keys()
    if missing:
        raise ValueError(f"Missing required keys: {sorted(missing)}")

    if not isinstance(config['question'], str):
        raise ValueError(f"'question' must be a string, got {type(config['question']).__name__}")

    if not isinstance(config['answer'], (str, dict)):
        raise ValueError(f"'answer' must be a string or dict, got {type(config['answer']).__name__}")


def _validate_regex(regex: list) -> None:
    """Check that all regex entries are strings that compile without error.

    Args:
        regex: The regex list from a question config.

    Raises:
        ValueError: If any entry is not a string or fails to compile.
    """
    for i, pattern in enumerate(regex):
        if not isinstance(pattern, str):
            raise ValueError(f"regex[{i}] must be a string, got {type(pattern).__name__}")
        try:
            re.compile(pattern)
        except re.error as e:
            raise ValueError(f"regex[{i}] is not a valid regex pattern: {e}")


def _validate_logic(logic: list, regex_count: int) -> None:
    """Check that all logic rules are well-formed.

    Each rule must have exactly one of 'all' or 'any', a 'score' key,
    and indices that are within range of the regex list.

    Args:
        logic: The logic list from a question config.
        regex_count: The number of regex patterns, used to validate indices.

    Raises:
        ValueError: If any rule is malformed.
    """
    for i, rule in enumerate(logic):
        if not isinstance(rule, dict):
            raise ValueError(f"logic[{i}] must be a dict, got {type(rule).__name__}")

        has_all = 'all' in rule
        has_any = 'any' in rule

        if not has_all and not has_any:
            raise ValueError(f"logic[{i}] must have either an 'all' or 'any' key")

        if has_all and has_any:
            raise ValueError(f"logic[{i}] must have 'all' or 'any' but not both")

        if 'score' not in rule:
            raise ValueError(f"logic[{i}] is missing required key 'score'")

        if not isinstance(rule['score'], int):
            raise ValueError(f"logic[{i}]['score'] must be an int, got {type(rule['score']).__name__}")

        key = 'all' if has_all else 'any'
        indices = rule[key]

        if not isinstance(indices, list) or len(indices) == 0:
            raise ValueError(f"logic[{i}]['{key}'] must be a non-empty list")

        for j, idx in enumerate(indices):
            if not isinstance(idx, int):
                raise ValueError(f"logic[{i}]['{key}'][{j}] must be an int, got {type(idx).__name__}")
            if idx < 0 or idx >= regex_count:
                raise ValueError(
                    f"logic[{i}]['{key}'][{j}] index {idx} is out of range "
                    f"for regex list of length {regex_count}"
                )


def validate(config: dict) -> None:
    """Validate a question config dict before compilation.

    Checks structure, regex patterns, and logic rules. Raises a ValueError
    with a descriptive message if anything is wrong. Returns cleanly if
    the config is valid.

    Call this before compile_question() to catch malformed configs early.

    Args:
        config: A single question entry from answers.json.

    Raises:
        ValueError: If the config is malformed in any way.
    """
    _validate_structure(config)
    if 'regex' in config:
        _validate_regex(config['regex'])
        if 'logic' not in config:
            raise ValueError("Questions with 'regex' must also have 'logic'")
        _validate_logic(config['logic'], len(config['regex']))


def validate_all(configs: dict) -> None:
    """Validate all question configs in an answers.json dict.

    Iterates over all questions and collects all validation errors before
    raising, so you see every problem at once rather than one at a time.

    Args:
        configs: The full answers.json dict, keyed by question number string.

    Raises:
        ValueError: If any config is malformed, with all errors listed.
    """
    errors = []
    for key, config in configs.items():
        try:
            validate(config)
        except ValueError as e:
            errors.append(f"Question {key}: {e}")

    if errors:
        raise ValueError("Invalid question configs:\n" + "\n".join(errors))