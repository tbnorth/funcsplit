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

    def visit(self, node, depth=0):
        """reuse of names is a problem, reset on assignment?"""
        names = set()

        if isinstance(node, ast.Name):
            names.add(node.id)

        line_names = defaultdict(set)
        for child in ast.iter_child_nodes(node):
            child_names = self.visit(child, depth=depth + 1)
            names.update(child_names)
            if hasattr(child, 'lineno'):
                line_names[child.lineno].update(child_names)

        if depth != self.report_depth:
            return names

        minmax = {}
        for line, names in line_names.items():
            for name in names:
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

        return names


top = ast.parse('\n'.join(lines))

nc = NameCounter()

nc.visit(top)
# print(ast.dump(top))
