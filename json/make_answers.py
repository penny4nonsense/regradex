"""
make_answers.py
---------------
Builds answers.json for Exam 1.

This script defines the questions, correct answers, regex patterns, and
scoring logic for each autograded question. Run it to regenerate answers.json
from scratch.

    python json/make_answers.py

The output file answers.json is read by the grading notebook. It is not
committed to the repository — see .gitignore.

Regex patterns are built using the regradex.helpers toolkit. Each pattern
corresponds to one element of the regex list in answers.json, and is
referenced by index in the logic rules.
"""

import json
from regradex.helpers import (
    case_ignore,
    white_ignore,
    before,
    and_,
    or_,
    opt,
)


# ---------------------------------------------------------------------------
# Shared building blocks
# ---------------------------------------------------------------------------

# Single digit
d = r'\d'

# Optional whitespace
s = opt(r'\s')

# Optional comma (thousands separator)
oc = opt(r'\,')

# Decimal point
p = r'\.'

# Three digits
d3 = d + d + d

# Zero or more digits
ds = d + '*'

# Optional decimal point
op = opt(p)

# T or K (thousands abbreviation)
tk = or_([case_ignore('t'), case_ignore('k')])

# M (millions abbreviation)
m = case_ignore('m')

# Dollar indicators
dollar_list = [r'\$', case_ignore('usd'), case_ignore('dol')]

# Thousands expressions: "thousand", "$k", "k$", "k usd", etc.
thousands = or_(
    [case_ignore('thou'), r'\$' + s + tk] +
    [tk + s + item for item in dollar_list]
)

# Millions expressions: "million", "$m", "m$", "m usd", etc.
millions = or_(
    [case_ignore('mill'), r'\$' + s + m] +
    [m + s + item for item in dollar_list]
)

# Dollar sign or word
dollars = or_(dollar_list)

# Percent sign or word
pct = or_(['%', case_ignore('perc')])

# "1" or "one" (for "1% increase" style answers)
unit = or_(['1', case_ignore('one')])

# "1%" or "one percent"
unitpct = unit + s + pct


# ---------------------------------------------------------------------------
# Questions and answers
# ---------------------------------------------------------------------------

question_numbers = [6, 9, 10, 11, 12, 13, 14, 15, 16, 17, 20, 21, 22, 23,
                    29, 30, 31, 32, 35, 36]

data = {str(i): {} for i in question_numbers}

questions = {
    '6':  "What's the average wage in the sample? What's the standard deviation of the wage?",
    '9':  "Interpret the estimated coefficient on age in modela.",
    '10': "Using modela, predict the estimated wage for a player who is 27 years old, has a draft number=7, and scores 5 points per game.",
    '11': "Using modela, predict the estimated wage for a player who is 27 years old, has a draft number=28, and scores 14 points per game.",
    '12': "Using modelb, when is the coefficient on minutes statistically significant?",
    '13': "What complicated hypothesis is being tested in modelc?",
    '14': "What is the result of the complicated hypothesis test in modelc?",
    '15': "What hypothesis is being tested in the anova with modeld?",
    '16': "What is the result of that anova test with modeld?",
    '17': "In modeld, what's a 95% confidence interval for a player who is 27 years old, plays 1800 minutes per year, scores 11 points per game, and has a draft number=20?",
    '20': "Using modelf, if the draft number increases by 1 position, what effect will that have on wage if draft=10?",
    '21': "Interpret the estimated coefficient on age in modelg.",
    '22': "Interpret the estimated coefficient on minutes in modelg.",
    '23': "White-corrected standard errors does NOT change the significance of any variables (one or more) in the model. (True or False)",
    '29': "Interpret the estimated coefficient on CPI in modela. Does the model make sense?",
    '30': "Which model is best?",
    '31': "Interpret the estimated coefficient on CPI in the model you have selected.",
    '32': "At what level is the coefficient on CPI significant in the model you have selected?",
    '35': "When is unemployment stationary?",
    '36': "When is the CPI stationary?",
}

answers = {
    '6':  '$1532700/year, $996567.1/year',
    '9':  '1 year increase in age ==> $91300/year in wage',
    '10': '$1117662/year',
    '11': '$1686348/year',
    '12': 'Sign at 5%, not at 1%',
    '13': 'b_4=b_5 or the coefficient on assists is equal the coefficient on rebounds',
    '14': 'Insign at 10%',
    '15': 'b_4=b_5=0 or joint significance of rebounds and assists',
    '16': 'Sign at 0.1%',
    '17': '$1421000/year to $1597000/year',
    '20': '-$27909/year',
    '21': '1% increase in age ==> 1.77% increase in wage',
    '22': '1 more minute ==> 0.00637% increase in wage',
    '23': 'False',
    '29': '1% increase in cpi ==> 0.0822% increase in unemployment. No. Spurious',
    '30': 'modelf',
    '31': {
        'modeld': '1% increase in cpi ==> 0.002% decrease in unemployment. Yes.',
        'modele': '1% increase in cpi ==> 2.079% decrease in unemployment. Yes.',
        'modelf': '1% increase in cpi ==> 0.801% decrease in unemployment. Yes.',
        'modelh': '1% increase in cpi ==> 0.682% decrease in unemployment. Yes.',
        'modeli': '1% increase in cpi ==> 3.018% decrease in unemployment. Yes.',
    },
    '32': 'Insign at 10%',
    '35': '1 difference, level',
    '36': '2 differences, level',
}

for i in questions:
    data[i]['question'] = questions[i]
    data[i]['answer'] = answers[i]


# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------
# Each entry in regex_dict is a list of patterns for that question.
# Patterns are referenced by index in the logic rules below.

regex_dict = {}

# Q6: Average wage ($1,532,700) and std deviation ($996,567)
# Pattern 0: mean expressed in full dollars (e.g. $1,532,700)
# Pattern 1: mean expressed in thousands (e.g. 1,532 thousand)
# Pattern 2: mean expressed in millions (e.g. 1.5 million)
# Pattern 3: std expressed in full dollars (e.g. $996,567)
# Pattern 4: std expressed in thousands (e.g. 996 thousand)
# Pattern 5: std expressed in millions (e.g. 0.99 million)
mean_patterns = [
    and_(['1' + oc + '5' + d + d + oc + d3, dollars]),
    and_(['1' + oc + '5' + d + d + op,      thousands]),
    and_(['1' + p + '5',                     millions]),
]
std_patterns = [
    and_(['99' + d + oc + d3, dollars]),
    and_(['99' + d + op,      thousands]),
    and_([p + '99',           millions]),
]
regex_dict[6] = [or_(mean_patterns), or_(std_patterns)]

# Q9: Coefficient on age — $91,300/year increase
# Pattern 0: word "year" present
# Pattern 1: number 91 with thousands or decimal
# Pattern 2: year appears before the number (e.g. "per year ... 91")
# Pattern 3: number 91 in any form
left = case_ignore('year')
other = ['91' + oc + d3, '91' + p]
right = [other[0], and_([other[1], thousands])]
combo = or_([before(left, item) for item in other])
regex_dict[9] = [left, or_(right), combo, or_(other)]

# Q10: Predicted wage $1,117,662
# Pattern 0: number in full dollars with unit
# Pattern 1: number in millions with unit
# Pattern 2: number in any form
x = lambda y: '1' + y + '1' + d + d
y = lambda z: '2' + z + '8' + d + d
w = lambda f: [
    or_([f(oc) + oc + d3, f(oc) + op + ds + s + case_ignore('k')]),
    f(oc) + op,
    f(p)
]
z = lambda f: [and_([w(f)[i], val]) for i, val in enumerate(['.', thousands, millions])]
regex_dict[10] = [or_(z(x)), or_(z(y)), or_(w(x))]

# Q11: Predicted wage $1,686,348
# Pattern 0: number in full dollars with unit
# Pattern 1: number in millions with unit
# Pattern 2: number in any form
x = lambda y: '1' + y + '[67]' + d + d
y = lambda z: '3' + z + '4' + d + d
regex_dict[11] = [or_(z(x)), or_(z(y)), or_(w(x))]

# Q13: Hypothesis b_4=b_5 (coefficient on assists equals coefficient on rebounds)
# Pattern 0: beta 4 referenced (b4, beta4, or "rebounds")
# Pattern 1: beta 5 referenced (b5, beta5, or "assists")
# Pattern 2: equality expressed ("equal" or "=")
b4 = or_(['[Bbß]' + opt('_') + '4',
           case_ignore('beta') + opt('_') + '4',
           case_ignore('rebo')])
b5 = or_(['[Bbß]' + opt('_') + '5',
           case_ignore('beta') + opt('_') + '5',
           case_ignore('assi')])
regex_dict[13] = [b4, b5, or_([case_ignore('equal'), '='])]

# Q15: Joint hypothesis b_4=b_5=0
# Pattern 0: beta 4 referenced
# Pattern 1: beta 5 referenced
# Pattern 2: equality or joint significance referenced
regex_dict[15] = [b4, b5, or_([regex_dict[13][2], case_ignore('joint')])]

# Q17: Confidence interval $1,421,000 to $1,597,000
# Pattern 0: lower bound in dollars or thousands
# Pattern 1: upper bound in millions
# Pattern 2: both bounds present
x = lambda y: '1' + y + '42' + d
y = lambda z: '1' + z + '[56][90]' + d
regex_dict[17] = [or_(z(x)), or_(z(y)), and_([x(oc), y(oc)])]

# Q20: Effect on wage — negative $27,909
# Pattern 0: number 27-31 in any form
# Pattern 1: negative sign or word
# Pattern 2: number in any form (looser match)
x = '2[6789]'
y = '3[01]'
z2 = lambda v: [or_([v + oc + d3, v + op + ds + s + case_ignore('k')]),
                and_([v + op, thousands])]
regex_dict[20] = [
    or_(z2(x) + z2(y)),
    or_([r'\-', case_ignore('neg'), case_ignore('dec')]),
    or_([x + op, y + op])
]

# Q21: Coefficient on age in log-log model — 1.77% increase per 1% increase in age
# Pattern 0: "1%" or "one percent" present
# Pattern 1: number 1.7x present before a percent sign
# Pattern 2: both present
x = f'1{p}[78]'
y = before(f'1{p}[78]', pct)
regex_dict[21] = [unitpct, y, before(unitpct, y)]

# Q22: Coefficient on minutes — 0.00637% increase per minute
# Pattern 0: "one minute" or "1 minute" present
# Pattern 1: number .006x present before percent sign
# Pattern 2: both present
x = before(p + '006', pct)
y = before(unit, case_ignore('min'))
regex_dict[22] = [y, x, before(y, x)]

# Q29: CPI coefficient — 0.0822% increase in unemployment per 1% increase in CPI
# Pattern 0: "1%" or "one percent" present
# Pattern 1: number .08x present before percent sign
# Pattern 2: both present
# Pattern 3: number .08x followed directly by percent (less strict)
x = p + '08'
y = before(x, pct)
regex_dict[29] = [unitpct, y, before(unitpct, y), x + ds + s + pct]

# Q31: CPI coefficient in selected model (multiple acceptable answers by model)
# Pattern 0: "1%" or "one percent" present
# Pattern 1: any of the model-specific coefficients present before percent
# Pattern 2: both pattern 0 and one of the model coefficients present
left = unitpct
right = {
    'modeld': p + '00[12]',
    'modele': f'2{p}[01]',
    'modelf': p + '8',
    'modelh': p + '[67]',
    'modeli': f'3{p}0',
}
right = {key: before(value, pct) for key, value in right.items()}
combo = {key: before(left, value) for key, value in right.items()}
regex_dict[31] = [left, or_(right.values()), or_(combo.values())]

# Q35: When is unemployment stationary? (1 difference, level)
# Pattern 0: "one difference", "first difference", "1st difference" etc.
# Pattern 1: word "level" present
diff = case_ignore('diff')
level = case_ignore('level')
diffs = or_([unit + s + diff, case_ignore('first'), '1' + case_ignore('st'),
             before(diff, unit)])
regex_dict[35] = [diffs, level]

# Q36: When is CPI stationary? (2 differences, level)
# Pattern 0: "two differences", "second difference", "2nd difference" etc.
# Pattern 1: word "level" present
two = or_([case_ignore('two'), '2'])
diffs = or_([two + s + diff, case_ignore('seco'), '2' + case_ignore('nd'),
             before(diff, two)])
regex_dict[36] = [diffs, level]

for i in regex_dict:
    data[str(i)]['regex'] = regex_dict[i]


# ---------------------------------------------------------------------------
# Logic rules
# ---------------------------------------------------------------------------
# Rules are evaluated in order. First match wins.
# 'all': all listed pattern indices must match.
# 'any': at least one listed pattern index must match.
# score: 0 from a matched rule means recognized wrong — not manual review.

logic_dict = {}

logic_dict[6] = [
    {'all': [0, 1], 'score': 10},  # both mean and std correct
    {'any': [0],    'score': 5},   # mean only
]
logic_dict[9] = [
    {'all': [0, 1, 2], 'score': 10},  # year, number, and year-before-number
    {'all': [0, 1],    'score': 10},  # year and number present
    {'any': [2],       'score': 5},   # year-before-number structure only
    {'any': [3],       'score': 5},   # number present in any form
]
logic_dict[10] = [
    {'any': [0], 'score': 10},  # full dollar amount
    {'any': [2], 'score': 5},   # number in any form
    {'any': [1], 'score': 5},   # millions form
]
logic_dict[11] = [
    {'any': [0], 'score': 10},
    {'any': [2], 'score': 5},
    {'any': [1], 'score': 5},
]
logic_dict[13] = [
    {'all': [0, 1, 2], 'score': 10},  # both betas and equality
    {'all': [0, 1],    'score': 0},   # both betas but no equality — recognized wrong
    {'any': [2],       'score': 0},   # equality only — recognized wrong
]
logic_dict[15] = [
    {'all': [0, 1, 2], 'score': 10},  # both betas and joint/equality
    {'all': [0, 1],    'score': 10},  # both betas (joint implied)
    {'any': [2],       'score': 0},   # equality/joint only — recognized wrong
]
logic_dict[17] = [
    {'all': [0, 1],    'score': 10},  # both bounds correct
    {'any': [2],       'score': 5},   # both numbers present but not confirmed as bounds
    {'any': [0, 1],    'score': 0},   # one bound only — recognized wrong
]
logic_dict[20] = [
    {'all': [0, 1], 'score': 10},   # correct number and negative sign
    {'all': [1, 2], 'score': 5},    # negative sign and approximate number
    {'any': [0, 2], 'score': 10},   # number present (note: review logic_dict[20] rule order)
]
logic_dict[21] = [
    {'all': [0, 1, 2], 'score': 10},  # "1%" and "1.7x%" both present
    {'all': [0, 1],    'score': 0},   # recognized wrong
]
logic_dict[22] = [
    {'all': [0, 1, 2], 'score': 10},  # minute and .006x% both present
    {'any': [1],       'score': 0},   # recognized wrong
]
logic_dict[29] = [
    {'all': [0, 1, 2], 'score': 10},  # "1%", ".08x%", and both together
    {'any': [3],       'score': 5},   # .08x followed by percent (partial)
    {'any': [1],       'score': 0},   # recognized wrong
]
logic_dict[31] = [
    {'all': [0, 1, 2], 'score': 10},  # "1%" and model-specific coefficient
    {'any': [1],       'score': 5},   # model-specific coefficient only
]
logic_dict[35] = [
    {'all': [0, 1], 'score': 10},  # differences and level both mentioned
    {'any': [0],    'score': 10},  # differences mentioned (level implied)
]
logic_dict[36] = [
    {'all': [0, 1], 'score': 10},
    {'any': [0],    'score': 10},
]

for i in logic_dict:
    data[str(i)]['logic'] = logic_dict[i]


# ---------------------------------------------------------------------------
# Write output
# ---------------------------------------------------------------------------

output_path = 'answers.json'
with open(output_path, 'w') as f:
    json.dump(data, f, indent=4)

print(f'Written to {output_path}')
print(f'Questions: {len(data)}')
print(f'Autograded: {sum(1 for v in data.values() if "regex" in v)}')
print(f'Manual only: {sum(1 for v in data.values() if "regex" not in v)}')