"""
helpers.py
----------
Regex pattern building utilities for regradex.

These helpers let you compose flexible answer-matching patterns from
readable building blocks without writing raw regex by hand.

All functions take strings and return strings. Patterns are not compiled
here — pass the result to re.compile() or include it in answers.json
where it will be compiled by compile_question().

Example usage:

    from regradex.helpers import case_ignore, or_, and_, opt

    d = r'\\d'
    thousands = or_([case_ignore('thou'), r'\\$\\s*k', r'k\\s*\\$'])
    amount = d + d + d + opt(r'\\,') + d + d + d
    pattern = and_([amount, thousands])

This produces a pattern matching "1,532 thousand", "$1532k", and similar.
"""


def case_ignore(x: str) -> str:
    """Match a string case-insensitively by wrapping each character in a character class.

    Args:
        x: The string to match case-insensitively.

    Returns:
        A regex pattern matching x in any combination of upper and lower case.

    Example:
        case_ignore("usd") -> "[Uu][Ss][Dd]"
    """
    return ''.join(f'[{c.upper()}{c.lower()}]' for c in x)


def white_ignore(x: str) -> str:
    """Append a zero-or-more whitespace matcher to a pattern.

    Useful for making patterns tolerant of spaces between tokens.

    Args:
        x: A regex pattern string.

    Returns:
        The pattern followed by \\s*.

    Example:
        white_ignore(r"\\$") -> "\\$\\s*"
    """
    return f'{x}\\s*'


def before(x: str, y: str) -> str:
    """Match x only when followed anywhere by y (lookahead).

    Args:
        x: The pattern that must be present.
        y: The pattern that must appear somewhere after x.

    Returns:
        A regex pattern using a lookahead assertion.

    Example:
        before(r"\\d+", r"dollars") -> "\\d+(?=.*dollars)"
    """
    return f'{x}(?=.*{y})'


def look_behind(x: str) -> str:
    """Match a position immediately preceded by x (lookbehind).

    Args:
        x: The pattern that must appear immediately before the match position.

    Returns:
        A lookbehind assertion pattern.

    Example:
        look_behind(r"\\$") -> "(?<=\\$)"
    """
    return f'(?<={x})'


def and_(patterns: list[str]) -> str:
    """Match a string that contains all of the given patterns (in any order).

    Uses lookahead assertions so the patterns can appear anywhere in the string
    and in any order.

    Args:
        patterns: List of regex pattern strings, all of which must match.

    Returns:
        A combined pattern using lookahead assertions.

    Example:
        and_([r"\\d+", r"dollars"]) -> "(?=.*\\d+)(?=.*dollars)"
    """
    return ''.join(f'(?=.*{p})' for p in patterns)


def or_(patterns: list[str]) -> str:
    """Match a string that contains at least one of the given patterns.

    Args:
        patterns: List of regex pattern strings, at least one of which must match.

    Returns:
        A combined alternation pattern.

    Example:
        or_([r"\\$", "dollars"]) -> "(\\$|dollars)"
    """
    return '(' + '|'.join(patterns) + ')'


def neg(x: str) -> str:
    """Negative lookahead — match a position not followed by x.

    Args:
        x: The pattern that must NOT appear at this position.

    Returns:
        A negative lookahead assertion pattern.

    Example:
        neg(r"\\d") -> "(?!\\d)"
    """
    return f'(?!{x})'


def opt(x: str) -> str:
    """Make a character or character class optional.

    Args:
        x: A single character or character class to make optional.

    Returns:
        A pattern matching x zero or one times.

    Example:
        opt(r"\\,") -> "[\\,]?"
    """
    return f'[{x}]?'


def starts_with(x: str) -> str:
    """Anchor a pattern to the start of the string.

    Args:
        x: The pattern that must appear at the start.

    Returns:
        The pattern anchored with ^.

    Example:
        starts_with(r"\\d+") -> "^\\d+"
    """
    return f'^{x}'


def ends_with(x: str) -> str:
    """Anchor a pattern to the end of the string.

    Args:
        x: The pattern that must appear at the end.

    Returns:
        The pattern anchored with $.

    Example:
        ends_with(r"\\d+") -> "\\d+$"
    """
    return f'{x}$'


def exact(x: str) -> str:
    """Match a pattern against the entire string.

    Args:
        x: The pattern that must match the full string.

    Returns:
        The pattern anchored at both start and end.

    Example:
        exact(r"\\d+") -> "^\\d+$"
    """
    return f'^{x}$'


def range_reps(x: str, n: int, m: int) -> str:
    """Match a pattern repeated between n and m times.

    Args:
        x: The pattern to repeat.
        n: Minimum number of repetitions.
        m: Maximum number of repetitions.

    Returns:
        A quantified pattern.

    Example:
        range_reps(r"\\d", 2, 4) -> "\\d{2,4}"
    """
    return f'{x}{{{n},{m}}}'


def zero_or_more(x: str) -> str:
    """Match a pattern zero or more times.

    Args:
        x: The pattern to repeat.

    Returns:
        The pattern with a * quantifier.

    Example:
        zero_or_more(r"\\d") -> "\\d*"
    """
    return f'{x}*'


def one_or_more(x: str) -> str:
    """Match a pattern one or more times.

    Args:
        x: The pattern to repeat.

    Returns:
        The pattern with a + quantifier.

    Example:
        one_or_more(r"\\d") -> "\\d+"
    """
    return f'{x}+'


def noncapturing(x: str) -> str:
    """Wrap a pattern in a non-capturing group.

    Useful for grouping without affecting match groups or backreferences.

    Args:
        x: The pattern to wrap.

    Returns:
        The pattern wrapped in a non-capturing group.

    Example:
        noncapturing(r"\\d+|\\w+") -> "(?:\\d+|\\w+)"
    """
    return f'(?:{x})'