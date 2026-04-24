"""
test_helpers.py
---------------
Unit tests for regradex.helpers.

Each helper gets two kinds of tests:
- Output test: does it produce the correct pattern string?
- Functional test: does the resulting pattern match and reject correctly?
"""

import re
import pytest
from regradex.helpers import (
    case_ignore,
    white_ignore,
    before,
    look_behind,
    and_,
    or_,
    neg,
    opt,
    starts_with,
    ends_with,
    exact,
    range_reps,
    zero_or_more,
    one_or_more,
    noncapturing,
)


# ---------------------------------------------------------------------------
# case_ignore
# ---------------------------------------------------------------------------

class TestCaseIgnore:

    def test_output(self):
        assert case_ignore('usd') == '[Uu][Ss][Dd]'

    def test_matches_lowercase(self):
        assert re.search(case_ignore('usd'), 'usd')

    def test_matches_uppercase(self):
        assert re.search(case_ignore('usd'), 'USD')

    def test_matches_mixed(self):
        assert re.search(case_ignore('usd'), 'Usd')

    def test_no_match(self):
        assert not re.search(case_ignore('usd'), 'eur')


# ---------------------------------------------------------------------------
# white_ignore
# ---------------------------------------------------------------------------

class TestWhiteIgnore:

    def test_output(self):
        assert white_ignore(r'\$') == r'\$\s*'

    def test_matches_no_space(self):
        assert re.search(white_ignore(r'\$') + r'\d', '$5')

    def test_matches_with_space(self):
        assert re.search(white_ignore(r'\$') + r'\d', '$ 5')

    def test_matches_multiple_spaces(self):
        assert re.search(white_ignore(r'\$') + r'\d', '$   5')


# ---------------------------------------------------------------------------
# before
# ---------------------------------------------------------------------------

class TestBefore:

    def test_output(self):
        assert before(r'\d+', 'dollars') == r'\d+(?=.*dollars)'

    def test_matches_when_y_follows(self):
        assert re.search(before(r'\d+', 'dollars'), '42 dollars')

    def test_no_match_when_y_absent(self):
        assert not re.search(before(r'\d+', 'dollars'), '42 euros')

    def test_y_can_appear_anywhere_after(self):
        assert re.search(before(r'\d+', 'dollars'), '42 US dollars please')


# ---------------------------------------------------------------------------
# look_behind
# ---------------------------------------------------------------------------

class TestLookBehind:

    def test_output(self):
        assert look_behind(r'\$') == r'(?<=\$)'

    def test_matches_after_prefix(self):
        assert re.search(look_behind(r'\$') + r'\d+', '$42')

    def test_no_match_without_prefix(self):
        assert not re.search(look_behind(r'\$') + r'\d+', '42')


# ---------------------------------------------------------------------------
# and_
# ---------------------------------------------------------------------------

class TestAnd:

    def test_output(self):
        assert and_([r'\d+', 'dollars']) == r'(?=.*\d+)(?=.*dollars)'

    def test_matches_when_all_present(self):
        assert re.search(and_([r'\d+', 'dollars']), '42 dollars')

    def test_no_match_when_one_missing(self):
        assert not re.search(and_([r'\d+', 'dollars']), '42 euros')

    def test_no_match_when_all_missing(self):
        assert not re.search(and_([r'\d+', 'dollars']), 'no answer')

    def test_order_independent(self):
        assert re.search(and_([r'\d+', 'dollars']), 'dollars 42')


# ---------------------------------------------------------------------------
# or_
# ---------------------------------------------------------------------------

class TestOr:

    def test_output(self):
        assert or_([r'\$', 'dollars']) == r'(\$|dollars)'

    def test_matches_first_option(self):
        assert re.search(or_([r'\$', 'dollars']), '$42')

    def test_matches_second_option(self):
        assert re.search(or_([r'\$', 'dollars']), '42 dollars')

    def test_no_match_when_none_present(self):
        assert not re.search(or_([r'\$', 'dollars']), '42 euros')


# ---------------------------------------------------------------------------
# neg
# ---------------------------------------------------------------------------

class TestNeg:

    def test_output(self):
        assert neg(r'\d') == r'(?!\d)'

    def test_matches_when_pattern_absent(self):
        assert re.search(neg(r'\d') + r'\w+', 'abc')

    def test_no_match_when_pattern_present(self):
        assert not re.search(neg(r'\d') + r'\d', '42')


# ---------------------------------------------------------------------------
# opt
# ---------------------------------------------------------------------------

class TestOpt:

    def test_output(self):
        assert opt(r'\,') == r'[\,]?'

    def test_matches_with_character(self):
        assert re.search(r'\d+' + opt(r'\,') + r'\d+', '1,532')

    def test_matches_without_character(self):
        assert re.search(r'\d+' + opt(r'\,') + r'\d+', '1532')


# ---------------------------------------------------------------------------
# starts_with
# ---------------------------------------------------------------------------

class TestStartsWith:

    def test_output(self):
        assert starts_with(r'\d+') == r'^\d+'

    def test_matches_at_start(self):
        assert re.search(starts_with(r'\d+'), '42 dollars')

    def test_no_match_not_at_start(self):
        assert not re.search(starts_with(r'\d+'), 'about 42 dollars')


# ---------------------------------------------------------------------------
# ends_with
# ---------------------------------------------------------------------------

class TestEndsWith:

    def test_output(self):
        assert ends_with(r'\d+') == r'\d+$'

    def test_matches_at_end(self):
        assert re.search(ends_with(r'\d+'), 'answer is 42')

    def test_no_match_not_at_end(self):
        assert not re.search(ends_with(r'\d+'), '42 dollars')


# ---------------------------------------------------------------------------
# exact
# ---------------------------------------------------------------------------

class TestExact:

    def test_output(self):
        assert exact(r'\d+') == r'^\d+$'

    def test_matches_full_string(self):
        assert re.search(exact(r'\d+'), '42')

    def test_no_match_with_extra_content(self):
        assert not re.search(exact(r'\d+'), '42 dollars')


# ---------------------------------------------------------------------------
# range_reps
# ---------------------------------------------------------------------------

class TestRangeReps:

    def test_output(self):
        assert range_reps(r'\d', 2, 4) == r'\d{2,4}'

    def test_matches_within_range(self):
        assert re.search(exact(range_reps(r'\d', 2, 4)), '42')
        assert re.search(exact(range_reps(r'\d', 2, 4)), '123')

    def test_no_match_below_range(self):
        assert not re.search(exact(range_reps(r'\d', 2, 4)), '1')

    def test_no_match_above_range(self):
        assert not re.search(exact(range_reps(r'\d', 2, 4)), '12345')


# ---------------------------------------------------------------------------
# zero_or_more
# ---------------------------------------------------------------------------

class TestZeroOrMore:

    def test_output(self):
        assert zero_or_more(r'\d') == r'\d*'

    def test_matches_zero(self):
        assert re.search(exact(zero_or_more(r'\d')), '')

    def test_matches_one(self):
        assert re.search(exact(zero_or_more(r'\d')), '4')

    def test_matches_many(self):
        assert re.search(exact(zero_or_more(r'\d')), '42')


# ---------------------------------------------------------------------------
# one_or_more
# ---------------------------------------------------------------------------

class TestOneOrMore:

    def test_output(self):
        assert one_or_more(r'\d') == r'\d+'

    def test_matches_one(self):
        assert re.search(exact(one_or_more(r'\d')), '4')

    def test_matches_many(self):
        assert re.search(exact(one_or_more(r'\d')), '42')

    def test_no_match_zero(self):
        assert not re.search(exact(one_or_more(r'\d')), '')


# ---------------------------------------------------------------------------
# noncapturing
# ---------------------------------------------------------------------------

class TestNoncapturing:

    def test_output(self):
        assert noncapturing(r'\d+|\w+') == r'(?:\d+|\w+'  ')'

    def test_does_not_create_capture_group(self):
        pattern = re.compile(noncapturing(r'\d+') + r'(\w+)')
        match = pattern.search('42abc')
        assert match is not None
        assert len(match.groups()) == 1  # only the explicit group, not the noncapturing one

    def test_matches_correctly(self):
        assert re.search(noncapturing(r'\d+|\w+'), '42')
        assert re.search(noncapturing(r'\d+|\w+'), 'abc')