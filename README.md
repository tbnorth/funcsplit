# funcsplit.py

So you wrote a Python function/method that's too long, and now you want
to split it.  Where - well, where the number of active variables is at a
minimum.  `funcsplit.py` uses [AST tree](https://docs.python.org/3/library/ast.html)
parsing to count the number of active variables (variables which will
be used again further down the function) on each line of the function.

For example, for code with a too complex function in lines 37-105:
```
python funcsplit.py <badcode.py

...
 43  2 i node
 46  2 i node
 50  2 node node_names
 52  3 __builtins__ node node_names
 59  3 line_names node node_names
 60  6 child child_names depth line_names node node_names
 66  3 depth line_names node_names
 69  3 line_names minmax node_names
 70  4 line_names minmax name_inc node_names
 72  8 line line_names minmax mode name name_inc names node_names
 87  4 breadth line_names minmax node_names
 88  8 breadth first last line line_names minmax name node_names
 93  4 breadth fmt node_names x
 95  4 breadth fmt line node_names
105  1 node_names
...
```

you can see there's a sweet spot for splitting the function between
line 66 (last time `depth` was referenced) and 69 (when `min_max` is first
defined).

