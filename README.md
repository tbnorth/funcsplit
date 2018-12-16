# funcsplit.py

So you wrote a Python function/method that's too long, and now you want to
split it.  But where? Well, where the number of active variables is at a
minimum.  `funcsplit.py` uses
[AST tree](https://docs.python.org/3/library/ast.html) parsing to count the
number of active variables (variables which will be used again further down the
function) on each line of the function.

Use
```
python funcsplit.py class < badcode.py
```
to scan `def`s withing classes, and just
```
python funcsplit.py < badcode.py
```
to scan module (top) level `def`s.

For example, for code with a too complex function in lines 37-105:
```
python funcsplit.py class < badcode.py

...
 43  2  0 i node
 46  2  1 i node
 50  2  1 node node_names
 52  3  2 __builtins__ node node_names
 59  3  2 line_names node node_names
 60  6  3 child child_names depth line_names node node_names
 66  3  3 depth line_names node_names
 69  3  2 line_names minmax node_names
 70  4  3 line_names minmax name_inc node_names
 72  8  4 line line_names minmax mode name name_inc names node_names
 87  4  3 breadth line_names minmax node_names
 88  8  4 breadth first last line line_names minmax name node_names
 93  4  2 breadth fmt node_names x
 95  4  3 breadth fmt line node_names
105  1  1 node_names
...
```

The numbers reported are line number, total variables, and variables carried
from the previous line.  You can see there's a sweet spot for splitting the
function between line 66 (last time `depth` was referenced) and 69 (when
`min_max` is first defined).
