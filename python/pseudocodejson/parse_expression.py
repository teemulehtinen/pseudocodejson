from . import parse_utils as u
from . import presentation as p

IGNORE_NODES = []
BUILT_IN_FUNCTIONS = [
  'abs', 'all', 'any', 'ascii', 'bin', 'bool', 'breakpoint', 'bytearray', 'bytes',
  'callable', 'chr', 'classmethod', 'compile', 'complex', 'delattr', 'dict', 'dir',
  'divmod', 'enumerate', 'eval', 'exec', 'filter', 'float', 'format', 'frozenset',
  'getattr', 'globals', 'hasattr', 'hash', 'help', 'hex', 'id', 'input', 'int',
  'isinstance', 'issubclass', 'iter', 'len', 'list', 'locals', 'map', 'max',
  'memoryview', 'min', 'next', 'object', 'oct', 'open', 'ord', 'pow', 'print',
  'property', 'range', 'repr', 'reversed', 'round', 'set', 'setattr', 'slice',
  'sorted', 'staticmethod', 'str', 'sum', 'super', 'tuple', 'type', 'vars', 'zip',
  '__import__'
]
OP_TABLE = {
  'And': 'and', 'Or': 'or',
  'Add': 'add', 'Sub': 'sub', 'Mult': 'mul', 'Div': 'div', 'Mod': 'mod',
  'Eq': 'equal',  'NotEq': 'different',
  'Gt': 'greater', 'GtE': 'greater_eq', 'Lt': 'smaller', 'LtE': 'smaller_eq',
}

def parse_expression(state, expr):
  u.require_expr(expr)
  type = u.node_type(expr)

  if type == 'Name':
    hit = state.find_variable_id(expr, expr.id, u.node_type(expr.ctx) != 'Store')
    if hit:
      return p.variable_expression(hit['uuid'])
    raise u.MissingNameError(expr.id)

  elif type == 'Call':
    u.require_type(expr.func, 'Name')
    hit = state.find_function_id(expr.func, expr.func.id, True)
    args = [parse_expression(state, a) for a in expr.args]
    if hit:
      return p.call_expression(hit['uuid'], args)
    if expr.func.id in BUILT_IN_FUNCTIONS:
      if expr.func.id == 'len':
        if len(expr.args) != 1:
          u.parse_error(expr, 'Expected exactly one argument')
        return p.array_length_expression(args[0])
      else:
        return p.call_builtin_expression(expr.func.id, args)
    raise u.MissingNameError(expr.func.id)

  elif type == 'NameConstant':
    return p.literal_expression('unknown', expr.value)

  elif type == 'Num':
    return p.literal_expression('int', expr.n)

  elif type == 'BinOp':
    op = u.node_type(expr.op)
    if op in OP_TABLE:
      return p.binary_operation(
        OP_TABLE[op],
        parse_expression(state, expr.left),
        parse_expression(state, expr.right)
      )
    u.unsupported_error(expr, "operation '{}'".format(op))

  elif type == 'Compare':
    if len(expr.ops) > 1:
      #TODO refactor a < b < c into a < b and b < c
      u.unsupported_error(expr, "chained comparison")
    op = u.node_type(expr.ops[0])
    if op in OP_TABLE:
      return p.binary_operation(
        OP_TABLE[op],
        parse_expression(state, expr.left),
        parse_expression(state, expr.comparators[0])
      )
    u.unsupported_error(expr, "operation '{}'".format(op))

  elif type == 'Subscript':
    u.require_type(expr.value, 'Name')
    u.require_type(expr.slice, 'Index')
    return p.array_element_expression(
      parse_expression(state, expr.value),
      parse_expression(state, expr.slice.value)
    )

  elif not type in IGNORE_NODES:
    raise u.unsupported_error(expr)

# expr = BoolOp(boolop op, expr* values)
#   | NamedExpr(expr target, expr value)
#   | BinOp(expr left, operator op, expr right)
#   | UnaryOp(unaryop op, expr operand)
#   | Lambda(arguments args, expr body)
#   | IfExp(expr test, expr body, expr orelse)
#   | Dict(expr* keys, expr* values)
#   | Set(expr* elts)
#   | ListComp(expr elt, comprehension* generators)
#   | SetComp(expr elt, comprehension* generators)
#   | DictComp(expr key, expr value, comprehension* generators)
#   | GeneratorExp(expr elt, comprehension* generators)
#
#   | Await(expr value)
#   | Yield(expr? value)
#   | YieldFrom(expr value)
#
#   | Compare(expr left, cmpop* ops, expr* comparators)
#   | Call(expr func, expr* args, keyword* keywords)
#   | FormattedValue(expr value, int? conversion, expr? format_spec)
#   | JoinedStr(expr* values)
#   | Constant(constant value, string? kind)
#
#   | Attribute(expr value, identifier attr, expr_context ctx)
#   | Subscript(expr value, expr slice, expr_context ctx)
#   | Starred(expr value, expr_context ctx)
#   | Name(identifier id, expr_context ctx)
#   | List(expr* elts, expr_context ctx)
#   | Tuple(expr* elts, expr_context ctx)
#
#   | Slice(expr? lower, expr? upper, expr? step)
