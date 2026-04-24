"""
test_schema.py
--------------
Unit tests for regradex.schema.

All tests are self-contained — no external files or data dependencies.
"""

import pytest
from regradex.schema import validate, validate_all


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def valid_config():
    """A fully valid question config dict."""
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
def valid_configs(valid_config):
    """A valid answers.json-style dict with multiple questions."""
    second = {
        'question': 'What is the unit?',
        'answer': 'dollars',
        'regex': [r'[Dd][Oo][Ll][Ll][Aa][Rr][Ss]'],
        'logic': [
            {'any': [0], 'score': 10},
        ]
    }
    return {'1': valid_config, '2': second}


# ---------------------------------------------------------------------------
# validate — happy path
# ---------------------------------------------------------------------------

class TestValidateHappyPath:

    def test_valid_config_passes(self, valid_config):
        validate(valid_config)  # should not raise

    def test_answer_as_dict_passes(self, valid_config):
        """answer can be a dict for questions with model-specific answers."""
        valid_config['answer'] = {'modela': '42 dollars', 'modelb': '43 dollars'}
        validate(valid_config)  # should not raise


# ---------------------------------------------------------------------------
# validate — structure
# ---------------------------------------------------------------------------

class TestValidateStructure:

    def test_missing_question(self, valid_config):
        del valid_config['question']
        with pytest.raises(ValueError, match="Missing required keys"):
            validate(valid_config)

    def test_missing_answer(self, valid_config):
        del valid_config['answer']
        with pytest.raises(ValueError, match="Missing required keys"):
            validate(valid_config)

    def test_missing_regex_is_valid(self, valid_config):
        """regex is optional — a question without it is manual-only."""
        del valid_config['regex']
        del valid_config['logic']
        validate(valid_config)  # should not raise

    def test_missing_logic_when_regex_present(self, valid_config):
        """If regex is present, logic is required."""
        del valid_config['logic']
        with pytest.raises(ValueError, match="must also have 'logic'"):
            validate(valid_config)

    def test_question_not_string(self, valid_config):
        valid_config['question'] = 42
        with pytest.raises(ValueError, match="'question' must be a string"):
            validate(valid_config)

    def test_regex_not_list(self, valid_config):
        valid_config['regex'] = r'\d+'
        with pytest.raises(ValueError, match="regex"):
            validate(valid_config)

    def test_regex_empty_list(self, valid_config):
        valid_config['regex'] = []
        with pytest.raises(ValueError, match="out of range"):
            validate(valid_config)

    def test_logic_not_list(self, valid_config):
        valid_config['logic'] = {'all': [0], 'score': 10}
        with pytest.raises(ValueError, match="must be a dict"):
            validate(valid_config)

    def test_logic_empty_list(self, valid_config):
        """Empty logic list is valid — no rules means everything goes to manual review."""
        valid_config['logic'] = []
        validate(valid_config)  # should not raise


# ---------------------------------------------------------------------------
# validate — regex patterns
# ---------------------------------------------------------------------------

class TestValidateRegex:

    def test_non_string_pattern(self, valid_config):
        valid_config['regex'] = [r'\d+', 42]
        with pytest.raises(ValueError, match="regex\\[1\\] must be a string"):
            validate(valid_config)

    def test_invalid_regex_pattern(self, valid_config):
        valid_config['regex'] = [r'\d+', '[']
        with pytest.raises(ValueError, match="regex\\[1\\] is not a valid regex pattern"):
            validate(valid_config)

    def test_valid_patterns_pass(self, valid_config):
        valid_config['regex'] = [r'\d+', r'[Dd][Oo][Ll]', r'(?=.*\d)']
        validate(valid_config)  # should not raise


# ---------------------------------------------------------------------------
# validate — logic rules
# ---------------------------------------------------------------------------

class TestValidateLogic:

    def test_rule_missing_all_and_any(self, valid_config):
        valid_config['logic'] = [{'score': 10}]
        with pytest.raises(ValueError, match="must have either an 'all' or 'any' key"):
            validate(valid_config)

    def test_rule_has_both_all_and_any(self, valid_config):
        valid_config['logic'] = [{'all': [0], 'any': [1], 'score': 10}]
        with pytest.raises(ValueError, match="must have 'all' or 'any' but not both"):
            validate(valid_config)

    def test_rule_missing_score(self, valid_config):
        valid_config['logic'] = [{'all': [0, 1]}]
        with pytest.raises(ValueError, match="missing required key 'score'"):
            validate(valid_config)

    def test_score_not_int(self, valid_config):
        valid_config['logic'] = [{'all': [0, 1], 'score': '10'}]
        with pytest.raises(ValueError, match="score.*must be an int"):
            validate(valid_config)

    def test_index_out_of_range(self, valid_config):
        valid_config['logic'] = [{'all': [0, 5], 'score': 10}]
        with pytest.raises(ValueError, match="index 5 is out of range"):
            validate(valid_config)

    def test_negative_index(self, valid_config):
        valid_config['logic'] = [{'all': [-1], 'score': 10}]
        with pytest.raises(ValueError, match="index -1 is out of range"):
            validate(valid_config)

    def test_empty_index_list(self, valid_config):
        valid_config['logic'] = [{'all': [], 'score': 10}]
        with pytest.raises(ValueError, match="must be a non-empty list"):
            validate(valid_config)

    def test_index_not_int(self, valid_config):
        valid_config['logic'] = [{'all': ['0'], 'score': 10}]
        with pytest.raises(ValueError, match="must be an int"):
            validate(valid_config)

    def test_rule_not_dict(self, valid_config):
        valid_config['logic'] = ['all: [0]']
        with pytest.raises(ValueError, match="must be a dict"):
            validate(valid_config)


# ---------------------------------------------------------------------------
# validate_all
# ---------------------------------------------------------------------------

class TestValidateAll:

    def test_all_valid_passes(self, valid_configs):
        validate_all(valid_configs)  # should not raise

    def test_single_invalid_raises(self, valid_configs):
        valid_configs['1']['regex'] = []
        with pytest.raises(ValueError, match="Question 1"):
            validate_all(valid_configs)

    def test_collects_all_errors(self, valid_configs):
        """All errors should be reported at once, not just the first."""
        valid_configs['1']['regex'] = [r'\d+']
        valid_configs['1']['logic'] = [{'all': [99], 'score': 10}]  # index out of range
        valid_configs['2']['logic'] = [{'score': 10}]  # missing all/any
        with pytest.raises(ValueError) as exc_info:
            validate_all(valid_configs)
        error_message = str(exc_info.value)
        assert 'Question 1' in error_message
        assert 'Question 2' in error_message

    def test_error_message_identifies_question(self, valid_configs):
        valid_configs['2']['logic'] = [{'score': 10}]
        with pytest.raises(ValueError, match="Question 2"):
            validate_all(valid_configs)