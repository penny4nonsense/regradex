# regradex

A regex-based autograder for short-answer quantitative exams, with tiered partial credit and a manual review queue for unrecognized responses.

---

## The idea

Most autograders give you a binary result — correct or incorrect. But marking an answer incorrect is a judgment call that deserves human attention. **regradex takes a different approach: it filters out answers that are clearly correct, and queues everything else for manual review. You never mark a student wrong without seeing their answer first.**

Correct answers are easy. A student who answered "$1,532,700/year" and a student who answered "1.5 million dollars per year" both got it right — they just expressed it differently. regradex handles that with flexible regex-based matching and tiered partial credit rules.

Incorrect answers are each a special case. Maybe the student had the right idea but made an arithmetic error. Maybe they misread the question. Maybe their answer is actually correct and your pattern just didn't catch it. regradex never decides that for you — it puts those answers in a queue for you to review.

This makes regradex a **partial autograder**. It does the filtering work so you can focus your attention where it matters.

---

## Installation

```bash
pip install regradex
```

Or for development:

```bash
git clone https://github.com/yourusername/regradex
cd regradex
pip install -e ".[dev]"
```

---

## Quick start

```python
import json
from regradex import validate_all, compile_question, autograde_all, review_queue, apply_manual, grade_all
import pandas as pd

# Load and validate your grading config
with open('answers.json') as f:
    configs = json.load(f)
validate_all(configs)

# Compile questions
questions = {key: compile_question(config) for key, config in configs.items()
             if 'regex' in config}

# Load student responses
df = pd.read_excel('Exam1.xlsx')

# Autograde
df = autograde_all(df, questions)

# Review unrecognized answers for question 6
queue = review_queue(df, '6')
for idx, answer in queue.items():
    print(f"Student {idx}: {answer}")
    score = int(input("Score: "))
    df = apply_manual(df, '6', idx, score)

# Compute final grades
df = grade_all(df, list(questions.keys()))
df.to_excel('results.xlsx', index=False)
```

---

## The config format

Grading logic lives in a JSON file — typically `answers.json`. Each key is a question number and each value is a question config.

```json
{
    "6": {
        "question": "What's the average wage in the sample? What's the standard deviation?",
        "answer": "$1,532,700/year, $996,567/year",
        "regex": [
            "(pattern matching $1,532,700 with dollar unit)",
            "(pattern matching 1,532 thousands)",
            "(pattern matching 1.5 millions)"
        ],
        "logic": [
            {"all": [0, 1], "score": 10},
            {"any": [0], "score": 5}
        ]
    }
}
```

Questions without a `regex` key are skipped by the autograder and go straight to manual review.

### The regex list

Each entry in `"regex"` is a pattern that matches one way of expressing a correct answer. The patterns are compiled once at load time and tested against every student response. The result is a boolean match vector — one `True` or `False` per pattern.

For example, if a question has three patterns and a student writes "1.5 million dollars":

```
regex[0] matches "$1,532,700"  -> False
regex[1] matches "thousands"   -> False
regex[2] matches "millions"    -> True

match vector: [False, False, True]
```

### The logic rules

Logic rules operate on the match vector by index. Each rule has either an `"all"` or `"any"` key containing a list of pattern indices, and a `"score"`.

- `"all": [0, 1]` — True if **every** listed index matched
- `"any": [0, 1]` — True if **at least one** listed index matched

Rules are evaluated in order and **the first matching rule wins**. This means you should put your highest-confidence, highest-score rules first.

A worked example for a question where the correct answer is "$1,532,700/year":

```json
"logic": [
    {"all": [0, 1], "score": 10},
    {"any": [0],    "score": 5}
]
```

In plain English:
- If the answer matches the full dollar format AND contains a thousands/millions qualifier → **10 points** (full credit)
- If the answer matches the number in any form → **5 points** (partial credit — right number, wrong unit)
- If nothing matches → **0, queued for manual review**

The key insight: a score of 0 from a matched rule means the answer was recognized as wrong. A score of 0 from no match means the answer was not recognized and needs a human to look at it. regradex tracks the difference.

### Partial credit

You can define as many scoring tiers as you need. Rules with `score: 0` are valid — they mean "I recognize this answer and it earns nothing", which is different from "I don't recognize this answer at all." Only unrecognized answers enter the manual review queue.

---

## The regex toolkit

Writing regex patterns by hand is painful. regradex ships with a set of helper functions that let you compose patterns from readable building blocks.

```python
from regradex.helpers import (
    case_ignore,      # case_ignore("usd")   -> [Uu][Ss][Dd]
    and_,             # and_([a, b])          -> (?=.*a)(?=.*b)
    or_,              # or_([a, b])           -> (a|b)
    opt,              # opt(r"\,")            -> [\,]?
    before,           # before(x, y)          -> x(?=.*y)
    neg,              # neg(x)                -> (?!x)
    one_or_more,      # one_or_more(x)        -> x+
    zero_or_more,     # zero_or_more(x)       -> x*
    noncapturing,     # noncapturing(x)       -> (?:x)
    exact,            # exact(x)              -> ^x$
    range_reps,       # range_reps(x, 2, 4)   -> x{2,4}
)
```

These are the same helpers used to build the patterns in `answers.json`. For example, matching a dollar amount expressed in thousands:

```python
d = r'\d'
thousands = or_([case_ignore('thou'), r'\$\s*k', r'k\s*\$'])
amount = d + d + d + opt(r'\,') + d + d + d
pattern = and_([amount, thousands])
```

Which produces a pattern that matches "1,532 thousand", "$1532k", "k$1532", and similar variations.

See `json/make_answers.py` for a complete example of how patterns are built for a real exam.

---

## Workflow

The typical grading workflow:

```
validate_all()       Catch config errors before you start
      ↓
compile_question()   Compile regex strings into pattern objects
      ↓
autograde_all()      Run the engine over every student response
      ↓
review_queue()       Get the answers that need human review (per question)
      ↓
apply_manual()       Record your judgment for each reviewed answer
      ↓
grade_all()          Compute final grades and totals
```

All functions return new dataframes — nothing mutates in place. Columns added by regradex use the `rg_` prefix by default (`rg_auto_N`, `rg_manual_N`, `rg_grade_N`, `rg_total`). The prefix is configurable if you need to avoid conflicts.

---

## Expected dataframe format

regradex expects a pandas dataframe with columns named `Answer N` for each question number N, matching the keys in your `answers.json`. This is the standard export format from most LMS platforms (Canvas, Blackboard, etc.).

---

## License

MIT