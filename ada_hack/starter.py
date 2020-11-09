import ast
import inspect
import json

class Backend(ast.NodeVisitor):
    def __init__(self):
        # initialize a way of recording information about nodes we visit
        # this just demonstrates a way to build up a data structure by
        # visiting python AST nodes.

        # note: we are not inferring bool vs int types, though it's probably possible to do
        self.stats = {"return": []}
        self.dump_dest = 'dump.json'
        self.dump = {'in': {}, 'out': 'int', 'locals': {}, 'statements': []}
        self.context_ptr = 0
        self.context_stack = [self.dump['statements']]

        # when we visit expressions, we write them here
        # so the outer statement can take them back
        self.last_expr = None

    def set_dest(self, filename):
        self.dump_dest = filename

    def enter(self, node):
        super().visit(node)
        with open('dump.json', 'w') as f:
            json.dump(self.dump, f, indent=4)

    def push_context(self, context):
        self.context_stack.append(context)
        self.context_ptr += 1

    def pop_context(self):
        self.context_stack.pop()
        self.context_ptr -= 1

    def append_stmt(self, stmt):
        self.context_stack[self.context_ptr].append(stmt)

    def update_locals(self, name, type_str='int'):
        if name in self.dump['locals']:
            return
        if name in self.dump['in']:
            return
        self.dump['locals'][name] = type_str

    def visit(self, node):
        # update the program dump as we visit nodes
        print('Debug: ', ast.dump(node))
        super().visit(node)
        
    def visit_Module(self, node):
        """
        The module is going to be the entry point;
        we expect it to contain exactly one function def and will freak out otherwise
        """
        body = node.body
        assert len(body) == 1
        assert isinstance(body[0], ast.FunctionDef)
        self.visit(body[0])

    def visit_FunctionDef(self, node):
        # we assume that this is the only function def
        # and it is the entry point to the program;
        # update the inputs and start recursing down the body

        args = [argument.arg for argument in node.args.args]
        body = node.body

        # we will want to update the inputs
        self.dump['in'] = {
            arg: 'int' for arg in args
        }

        for stmt in body:
            self.visit(stmt)

    def visit_While(self, node):
        if len(node.orelse) != 0:
            raise Exception('Do not support while-else (too confusing)')

        stmt = {
            "type": "while",
            "condition": {},
            "body": []
        }

        self.visit(node.test)
        stmt['condition'] = self.last_expr

        for body_stmt in node.body:
            self.push_context(stmt['body'])
            self.visit(body_stmt)
            self.pop_context()

        self.append_stmt(stmt)

    def visit_If(self, node):
        stmt = {
            "type": "if",
            "condition": {},
            "then_body": [],
            "else_body": []
        }

        self.visit(node.test)
        stmt['condition'] = self.last_expr

        for body_stmt in node.body:
            self.push_context(stmt['then_body'])
            self.visit(body_stmt)
            self.pop_context()

        for else_stmt in node.orelse:
            self.push_context(stmt['else_body'])
            self.visit(body_stmt)
            self.pop_context()            

        self.append_stmt(stmt)

    def visit_Constant(self, node):
        # note: it is unclear whether Python >=3.8 also handles "NameConstants"
        # using the constant node; if you are using the latest Python, please check
        self.last_expr = {
            "type": "const",
            "value": node.value
        }

    def visit_BinOp(self, node):
        ret = {
            "type": "binary",
            "op": "",
            "left": {},
            "right": {}
        }

        self.visit(node.left)
        lhs = self.last_expr
        ret['left'] = lhs
        self.visit(node.right)
        rhs = self.last_expr
        ret['right'] = rhs

        if isinstance(node.op, ast.Add):
            op_str = 'plus'
        elif isinstance(node.op, ast.Sub):
            op_str = 'minus'
        elif isinstance(node.op, ast.Mult):
            op_str = 'mult'
        # if you want to distinguish between floats and ints, then the distinction
        # between Div and FloorDiv is important, but we're not doing that right now
        elif isinstance(node.op, ast.Div) or isinstance(node.op, ast.FloorDiv):
            op_str = 'div'
        elif isinstance(node.op, ast.Mod):
            op_str = 'mod'
        elif isinstance(node.op, ast.Pow):
            op_str = 'power'
        elif isinstance(node.op, ast.LShift):
            op_str = 'left_shift'
        elif isinstance(node.op, ast.RShift):
            op_str = 'right_shift'
        # potentially, the lower level may not want to distinguish between
        # bitwise operators and boolean operators, but Python does distinguish
        elif isinstance(node.op, ast.BitOr):
            op_str = 'bitwise_or'
        elif isinstance(node.op, ast.BitAnd):
            op_str = 'bitwise_and'
        elif isinstance(node.op, ast.BitXor):
            op_str = 'xor'
        # probably not going to support this
        elif isinstance(node.op, ast.MatMult):
            op_str = 'matmult'
        ret['op'] = op_str

        self.last_expr = ret

    def visit_UnaryOp(self, node):
        ret = {
            "type": "unary",
            "value": {},
            "op": ""
        }

        self.visit(node.operand)
        ret['value'] = self.last_expr

        if isinstance(node.op, ast.UAdd):
            # kind of redundant, like writing out +1
            op_str = 'plus'
        elif isinstance(node.op, ast.USub):
            op_str = 'minus'
        # note: "not" is a boolean op and "invert" is bitwise
        elif isinstance(node.op, ast.Not):
            op_str = 'not'
        elif instance(node.op, ast.Invert):
            op_str = 'invert'

        self.last_expr = ret

    def visit_Name(self, node):
        name = node.id
        self.last_expr = {
            "type": "identifier",
            "name": name
        }

    def visit_Num(self, node):
        self.last_expr = {
            "type": "const",
            "value": node.n
        }

    def visit_Assign(self, node):
        stmt = {
            "type": "assignment",
            "name": "",
            "value": {}
        }

        targets = node.targets
        if len(targets) != 1:
            raise Exception('We only support single-target assignments')
        name = targets[0]
        if not isinstance(name, ast.Name):
            raise Exception('We only support assignments to identifiers')

        stmt['name'] = name.id
        self.update_locals(name.id)

        self.visit(node.value)
        stmt['value'] = self.last_expr
        self.append_stmt(stmt)

    def visit_AugAssign(self, node):
        """
        AugAssign(
            target=Name(id='x', ctx=Store()),
            op=Add(),
            value=Constant(value=2))
        ->
        Assign(
            targets=[Name(id='x', ctx=Store())],
            value=BinOp(
                left=Name(id='x', ctx=Load()),
                op=Add(),
                right=Constant(value=2)
            )
        )
        """

        # to avoid more complexity in the back-end, we just turn
        # augmented assignments into assignments with a binary op
        # (AKA turn x += 1 into x = x + 1)
        new_node = ast.Assign(
            targets=[node.target],
            value=ast.BinOp(
                left=ast.Name(id=node.target.id, ctx=ast.Load()),
                op=node.op,
                right=node.value
            )
        )
        self.visit(new_node)

    def visit_NameConstant(self, node):
        ret = {
            'type': 'const',
            'value': ''
        }
        if node.value is None:
            raise Exception('Do not support None values')
        if node.value is True:
            ret['value'] = 1
        elif node.value is False:
            ret['value'] = 0
        # in principle, we can try to infer what types must be bools from this
        self.last_expr = ret

    def visit_BoolOp(self, node):
        # Our representation treats boolean ops as ordinary binary ops
        # but Python's AST has a separate node for them
        ret = {
          'type': 'binary',
          'left': {},
          'right': {},
          'op': ''
        }

        # we are going to assume exactly two operands; 
        # in principle, it should be easy to turn an invocation with more operands
        # into a tree of binary invocations

        args = node.values
        if len(args) > 2:
            raise Exception('We only support exactly two operands in boolean op nodes')

        self.visit(args[0])
        lhs = self.last_expr
        ret['left'] = lhs
        self.visit(args[1])
        rhs = self.last_expr
        ret['right'] = rhs

        if isinstance(node.op, ast.And):
            op_str = 'and'
        elif isinstance(node.op, ast.Or):
            op_str = 'or'
        ret['op'] = op_str

        self.last_expr = ret

    def visit_Compare(self, node):
        # our representation treats these as binary ops,
        # but Python has a separate AST node for comparisons

        ret = {
          'type': 'binary',
          'left': {},
          'right': {},
          'op': ''
        }

        if len(node.ops) != 1 or len(node.comparators) != 1:
            raise Exception('Do not support having more than one serial comparison')
        
        self.visit(node.left)
        lhs = self.last_expr
        ret['left'] = lhs
        self.visit(node.comparators[0])
        rhs = self.last_expr
        ret['right'] = rhs
        
        op = node.ops[0]
        if isinstance(op, ast.Eq):
            op_str = "equals"
        elif isinstance(op, ast.NotEq):
            op_str = "not_equals"
        elif isinstance(op, ast.Lt):
            op_str = "lt"
        elif isinstance(op, ast.LtE):
            op_str = "lte"
        elif isinstance(op, ast.Gt):
            op_str = "gt"
        elif isinstance(op, ast.GTe):
            op_str = "gte"
        else:
            raise Exception(f'Do not support comparison {ast.dump(op)}')
        ret['op'] = op_str

        self.last_expr = ret

    def visit_Pass(self, node):
        print('Hit a pass')

    def visit_Return(self, node):
        """Override the return visitor method to record any return nodes
        that we visit."""
        self.stats["return"].append(node)
        stmt = {
            "type": "return",
            "value": {}
        }
        value = self.visit(node.value)
        stmt['value'] = self.last_expr
        self.append_stmt(stmt)

    def generic_visit(self, node):
        # we will reject anything we don't explicitly support
        raise Exception(f"Unsupported node: {ast.dump(node)}")

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
    b.enter(syn)

    # overwrite the annotated function to print the things
    # we've gathered from the visitor
    return b.report()


# transforms the function into a string
@futil
def foo(x):
    pass
    pass
    return x

@futil
def fibonacci(n):
    a = 0
    b = 1
    i = 0
    prev = 0
    while i < n:
        b = a + b
        a = prev
        prev = b
        i += 1
    return prev

def main():
    # foo is no longer a function, but a string
    print(fibonacci)


if __name__ == "__main__":
    main()
