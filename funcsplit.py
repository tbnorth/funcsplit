import keyword
import re
import sys

from logging import info

COMMON = "main os sys time namedtuple defaultdict"
COMMON = COMMON.split()

multi = lambda x: "(%s)" % '|'.join(r"\b%s\b" % i for i in x)

CULLS = [
    r"'[^']*'",  # things in 'quotes'
    r'"[^"]*"',  # things in "quotes"
    r"\W[0-9][0-9.]*",  # numbers
    r"\s*#.*",  # comments
    # keywords and constants
    multi(keyword.kwlist + ['True', 'False', 'None']),
    # builtins
    multi(dir(__builtins__)),
    # common modules / methods
    multi(COMMON),
]

# info('\n'.join(CULLS))

CULLS = [re.compile(i) for i in CULLS]

IDENTIFIER = re.compile(r"\b(?<!\.)(?<!for )[A-Za-z_]\w*")

test = "if a == True or otter12 is -13.6 * w"

lines = [i.strip() for i in sys.stdin]

# lines = [test]

for line_n, line in enumerate(lines):
    info(line)
    for cull_n, cull in enumerate(CULLS):
        line = cull.sub(' ', line)
        info(cull_n, line)
    line = IDENTIFIER.findall(line)
    info(line)
    lines[line_n] = line

print('\n'.join(map(str, lines)))
