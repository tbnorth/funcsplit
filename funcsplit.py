import ast
import sys

from collections import defaultdict

test = "if a == True or otter12 is -13.6 * w"

lines = [i.rstrip() for i in sys.stdin]

# lines = [test]


class NameCounter(ast.NodeVisitor):
    """Count names"""

    def __init__(self, *args, **kwargs):
        ast.NodeVisitor.__init__(self, *args, **kwargs)
        self.report_depth = 2

    def node_key(self, node):
        return "%s:%s" % (node.id, node.ctx.__class__.__name__)

    def visit(self, node, depth=0):
        """reuse of names is a problem, reset on assignment?

        i.e. when expr_context is Store?
        """
        node_names = set()

        if isinstance(node, ast.Name):
            node_names.add(self.node_key(node))
        i = len(node_names)

        line_names = defaultdict(set)
        for child in ast.iter_child_nodes(node):
            child_names = self.visit(child, depth=depth + 1)
            node_names.update(child_names)
            if hasattr(child, 'lineno'):
                line_names[child.lineno].update(child_names)

        if depth != self.report_depth:
            return node_names

        minmax = {}
        name_inc = defaultdict(lambda: 0)

        for line in sorted(line_names):
            names = line_names[line]
            for name in names:
                name, mode = name.split(':')
                if mode == 'Store':
                    name_inc[name] += 1
                name = "%s.%s" % (name, name_inc[name])
                if name not in minmax:
                    minmax[name] = (line, line)
                else:
                    minmax[name] = (
                        min(minmax[name][0], line),
                        max(minmax[name][1], line),
                    )
        # print('\n'.join(str(i) for i in minmax.items()))

        breadth = defaultdict(set)
        for line in line_names:
            for name, (first, last) in minmax.items():
                if first <= line <= last:
                    breadth[line].add(name)

        for line in sorted(breadth):
            print(line, len(breadth[line]), breadth[line])

        i = len(node_names)
        type(i)

        return node_names


top = ast.parse('\n'.join(lines))

nc = NameCounter()

nc.visit(top)
# print(ast.dump(top))
