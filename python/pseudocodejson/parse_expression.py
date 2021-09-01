from . import parse_utils as u
from . import presentation as p

IGNORE_NODES = []
BUILT_IN_VARIABLES = [
  '__name__'
]
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
  'Invert': 'minus', 'Not': 'not',
}


def parse_expression(state, expr):
  u.require_expr(expr)
  expr_type = u.node_type(expr)

  if expr_type == 'Name':
    hit = state.find_variable_id(expr, expr.id, u.node_type(expr.ctx) != 'Store')
    if hit:
      return p.variable_expression(hit['uuid'])
    if expr.id in BUILT_IN_VARIABLES:
      return p.builtin_variable_expression(expr.id)
    raise u.MissingNameError(expr.id)

  elif expr_type == 'Call':
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

  elif expr_type == 'NameConstant':
    if type(expr.value) == bool:
      return p.literal_expression('boolean', expr.value)
    else:
      u.unsupported_error(expr, "literal '{}'".format(expr.value))

  elif expr_type == 'Num':
    return p.literal_expression('int', expr.n)
  
  elif expr_type == 'Str':
    return p.literal_expression('string', expr.s)

  elif expr_type == 'BinOp':
    op = u.node_type(expr.op)
    if op in OP_TABLE:
      return p.binary_operation(
        OP_TABLE[op],
        parse_expression(state, expr.left),
        parse_expression(state, expr.right)
      )
    u.unsupported_error(expr, "operation '{}'".format(op))

  elif expr_type == 'UnaryOp':
    op = u.node_type(expr.op)
    if op in OP_TABLE:
      return p.unary_operation(
        OP_TABLE[op],
        parse_expression(state, expr.operand)
      )
    raise u.unsupported_error(expr, "operation '{}'".format(op))
  
  elif expr_type == 'BoolOp':
    op = u.node_type(expr.op)
    if op in OP_TABLE:
      return build_bool_tree(
        op,
        [parse_expression(state, e) for e in expr.values]
      )

  elif expr_type == 'Compare':
    return build_compare_tree(
      expr,
      parse_expression(state, expr.left),
      expr.ops,
      [parse_expression(state, e) for e in expr.comparators]
    )

  elif expr_type == 'Subscript':
    u.require_type(expr.value, 'Name')
    u.require_type(expr.slice, 'Index')
    return p.array_element_expression(
      parse_expression(state, expr.value),
      parse_expression(state, expr.slice.value)
    )

  elif expr_type in ('List', 'Tuple'):
    return p.literal_expression('array', list(parse_expression(state, e) for e in expr.elts))

  elif not expr_type in IGNORE_NODES:
    u.print_tree(expr)
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

def build_bool_tree(op, vals):
  if len(vals) > 2:
    return p.binary_operation(OP_TABLE[op], vals[0], build_bool_tree(op, vals[1:]))
  return p.binary_operation(OP_TABLE[op], vals[0], vals[1])

def build_compare_tree(expr, left, ops, comparators):
  op = u.node_type(ops[0])
  if op in OP_TABLE:
    cmp = p.binary_operation(OP_TABLE[op], left, comparators[0])
    if len(ops) > 1:
      return p.binary_operation(
        OP_TABLE['And'],
        cmp,
        build_compare_tree(expr, comparators[0], ops[1:], comparators[1:])
      )
    return cmp
  u.unsupported_error(expr, "operation '{}'".format(op))
