import ast
import sys

from collections import defaultdict

lines = [i.rstrip() for i in sys.stdin]


class NameCounter(ast.NodeVisitor):
    """Count names"""

    def __init__(self, *args, **kwargs):
        ast.NodeVisitor.__init__(self, *args, **kwargs)
        self.report_depth = 2
        self.imported = set(['self'])

    def node_key(self, node):
        """a = 7 -> a:Store, print(b) -> b:Load, so we can detect variable
        name reuse
        """
        return "%s:%s" % (node.id, node.ctx.__class__.__name__)

    def store_load(self, items):
        """if foo:Load and foo:Store both present, just report foo:Store"""
        culls = set()
        for item in items:
            name = item.split(':', 1)[0]
            if name + ':Store' in items and name + ':Load' in items:
                culls.add(name + ':Load')
        return items - culls

    def visit(self, node, depth=0):
        """reuse of names is a problem, reset on assignment?

        i.e. when expr_context is Store?
        """
        if isinstance(node, ast.Import):
            self.imported.update(i.asname or i.name for i in node.names)
            return set()
        if isinstance(node, ast.ImportFrom):
            self.imported.update(i.asname or i.name for i in node.names)
            return set()

        node_names = set()

        if (
            isinstance(node, ast.Name)
            and node.id not in dir(__builtins__)
            and node.id not in self.imported
        ):
            node_names.add(self.node_key(node))

        line_names = defaultdict(set)
        for child in ast.iter_child_nodes(node):
            child_names = self.visit(child, depth=depth + 1)
            node_names.update(child_names)
            if hasattr(child, 'lineno'):
                line_names[child.lineno].update(child_names)

        if depth != self.report_depth:
            return self.store_load(node_names)

        return self.proc_names(line_names, node_names)

    def proc_names(self, line_names, node_names):

        minmax = {}
        name_inc = defaultdict(lambda: 0)

        for line in sorted(line_names):
            names = line_names[line]
            for name in names:
                name, mode = name.split(':')
                if mode == 'Store' and name in name_inc:
                    name_inc[name] += 1
                name = "%s.%s" % (name, name_inc[name])
                if name not in minmax:
                    minmax[name] = (line, line)
                else:
                    minmax[name] = (
                        min(minmax[name][0], line),
                        max(minmax[name][1], line),
                    )

        breadth = defaultdict(set)
        for line in line_names:
            for name, (first, last) in minmax.items():
                if first <= line <= last:
                    breadth[line].add(name)

        fmt = lambda x: x.rsplit('.', 1)[0]
        # fmt = lambda x: x
        for line in sorted(breadth):
            print(
                "%3d %2d %s"
                % (
                    line,
                    len(breadth[line]),
                    ' '.join(sorted(map(fmt, breadth[line]))),
                )
            )

        return self.store_load(node_names)


top = ast.parse('\n'.join(lines))

nc = NameCounter()

nc.visit(top)
