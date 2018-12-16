# funcsplit.py

So you wrote a Python function/method that's too long, and now you want to
split it.  But where? Well, where the number of active variables is at a
minimum.  `funcsplit.py` uses
[AST tree](https://docs.python.org/3/library/ast.html) parsing to count the
number of active variables (variables which will be used again further down the
function) on each line of the function.

```
usage: funcsplit.py [-h] [--color] [--reuse] [depth]

Find places to split long functions / methods

positional arguments:
  depth       Reporting depth, 1 for module level functions, 2 for defs within
              classes (default: 1)

optional arguments:
  -h, --help  show this help message and exit
  --color     Use color output (default: False)
  --reuse     Show variable name reuse (i.0, i.1, etc.) (default: False)
```

For example, for code with a too complex function in lines 37-105:
```
python funcsplit.py 2 < funcsplit.py.comp
...
 43  2  0 i* node*
 46  2  1 i* node
 50  2  1 node node_names*
 52  3  2 __builtins__* node node_names
 59  3  2 line_names* node node_names
 60  6  3 child* child_names* depth* line_names node node_names
 66  3  3 depth line_names node_names
 69  3  2 line_names minmax* node_names
 70  4  3 line_names minmax name_inc* node_names
 72  8  4 line* line_names minmax mode* name* name_inc names* node_names
 87  4  3 breadth* line_names minmax node_names
 88  8  4 breadth first* last* line* line_names minmax name* node_names
 93  4  2 breadth fmt* node_names x*
 95  4  3 breadth fmt line* node_names
105  1  1 node_names
...
```

The numbers reported are line number, total variables, and variables carried
from the previous line.  `*` indicates variables added since the previous
reported line, use `--color` for green highlight instead.
You can see there's a sweet spot for splitting the
function between line 66 (last time `depth` was referenced) and 69 (when
`min_max` is first defined).

*NOTE:* on lines 43 and 46 `i` is listed as new both times, because the variable
name `i` has been reused.  Use `--reuse` to see this displayed as `i.0`, `i.1`, etc.


