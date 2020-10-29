import ast
import inspect


class Backend(ast.NodeVisitor):
    def __init__(self):
        # initialize a way of recording information about nodes we visit
        # this just demonstrates a way to build up a data structure by
        # visiting python AST nodes.
        self.stats = {"return": []}

    def visit_Return(self, node):
        """Override the return visitor method to record any return nodes
        that we visit."""
        self.stats["return"].append(node)
        self.generic_visit(node)

    def report(self):
        """Return some information that we gathered during the visit."""
        return str(self.stats)


def futil(f):
    # get the source of the function
    source = inspect.getsource(f)
    # parse the source into an ast
    syn = ast.parse(source)
    # initialize the visitor and call it on the function ast
    b = Backend()
    b.visit(syn)

    # overwrite the annotated function to print the things
    # we've gathered from the visitor
    return b.report()


# transforms the function into a string
@futil
def foo(x):
    return x


def main():
    # foo is no longer a function, but a string
    print(foo)


if __name__ == "__main__":
    main()
