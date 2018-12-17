import argparse
import ast
import sys

from collections import defaultdict, namedtuple

Output = namedtuple("Output", "line common diff")


class NameCounter(ast.NodeVisitor):
    """Count names"""

    def __init__(self, depth=1, color=False, reuse=False):
        ast.NodeVisitor.__init__(self)
        self.report_depth = depth
        self.imported = set(['self'])
        self.color = color
        self.reuse = reuse
        self.all_lines = []

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

    def fmt_list(self, output, color=None):
        if color is None:
            # allow vim_script to override user setting
            color = self.color
        if color:
            return self.fmt_list_color(output)
        else:
            return self.fmt_list_bw(output)

    def fmt_reuse(self, text):
        return text if self.reuse else text.rsplit('.', 1)[0]

    def fmt_list_bw(self, outline):
        return "%3d %2d %2d %s" % (
            outline.line,
            len(outline.common) + len(outline.diff),
            len(outline.common),
            ' '.join(
                sorted(
                    map(self.fmt_reuse, outline.common)
                    + [i + '*' for i in map(self.fmt_reuse, outline.diff)]
                )
            ),
        )

    def fmt_list_color(self, outline):
        colored = []
        for name in sorted(i for i in outline.common | outline.diff):
            colored.append(
                "\033[32m%s\033[0m" % self.fmt_reuse(name)
                if name in outline.diff
                else self.fmt_reuse(name)
            )
        return "%3d %2d %2d %s" % (
            outline.line,
            len(outline.common) + len(outline.diff),
            len(outline.common),
            ' '.join(colored),
        )

    def visit(self, node, depth=0):
        """Visit each node in AST tree"""
        if isinstance(node, ast.Import):
            self.imported.update(i.asname or i.name for i in node.names)
            return set()
        if isinstance(node, ast.ImportFrom):
            self.imported.update(i.asname or i.name for i in node.names)
            return set()

        node_names = set()

        if depth <= self.report_depth and isinstance(node, ast.Name):
            self.imported.add(node.id)

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

        if depth <= self.report_depth:
            self.proc_names(line_names, node_names)

        return self.store_load(node_names)

    def proc_names(self, line_names, node_names):
        """Analyze names and produce output"""

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

        prev = set()
        for line in sorted(breadth):
            common = prev & breadth[line]
            diff = breadth[line] - common
            output = Output(line, common, diff)
            print(self.fmt_list(output))
            self.all_lines.append(output)
            prev = breadth[line]

    def vim_script(self):
        scr = []
        tmpl = 'exe "sign place %d line=%d name=s%d file=" . expand("%%:p")'
        tmp2 = 'exe "cadde \\"" . expand("%%") . ":%d:%s\\""'

        # set of variable counts
        signs = set(len(i.common) for i in self.all_lines)
        scr.append("sign unplace *")
        scr.append("cexpr []")
        scr.append('set errorformat=%f:%l:%m')
        for sign in signs:
            # define sign `s12` with text "12"
            scr.append(
                "sign define s%s text=%s"
                % (sign, sign if sign < 100 else 'XX')
            )
        for n, output in enumerate(self.all_lines):
            scr.append(tmpl % (n + 1, output.line, len(output.common)))
            scr.append(
                tmp2
                % (output.line, self.fmt_list(output, color=False))
                # tmp2 % (output.line, 'ERR')
            )
        return '\n'.join(scr)


def make_parser():
    """prepare an argparse argument parser"""
    parser = argparse.ArgumentParser(
        description="""Find places to split long functions / methods""",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--color", action='store_true', help="Use color output", default=False
    )
    parser.add_argument(
        "--reuse",
        action='store_true',
        help="Show variable name reuse (i.0, i.1, etc.)",
        default=False,
    )
    parser.add_argument(
        "--vim-script",
        help="Write a script to FILE to display variable counts in Vim",
    )
    parser.add_argument(
        'depth',
        type=int,
        default=1,
        nargs='?',
        help="Reporting depth, 1 for module level functions, "
        "2 for defs within classes",
    )

    return parser


def get_options(args=None):
    """get_options - use argparse to parse args, and return a
    argparse.Namespace, possibly with some changes / expansions /
    validatations.

    Client code should call this method with args as per sys.argv[1:],
    rather than calling make_parser() directly.

    :param [str] args: arguments to parse
    :return: options with modifications / validations
    :rtype: argparse.Namespace
    """
    opt = make_parser().parse_args(args)

    # modifications / validations go here

    return opt


def main():
    opt = get_options()
    lines = [i.rstrip() for i in sys.stdin]
    top = ast.parse('\n'.join(lines))

    nc = NameCounter(depth=opt.depth, color=opt.color, reuse=opt.reuse)

    nc.visit(top)

    if opt.vim_script:
        with open(opt.vim_script, 'w') as out:
            out.write(nc.vim_script())


if __name__ == "__main__":
    main()
