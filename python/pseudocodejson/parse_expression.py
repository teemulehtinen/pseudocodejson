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
  '__import__', 'NotImplementedError'
]
BUILT_IN_VARIABLES = {
  '__name__': 'string'
}
OP_TABLE = {
  'And': 'and', 'Or': 'or',
  'Add': 'add', 'Sub': 'sub', 'Mult': 'mul', 'Div': 'div', 'FloorDiv': 'idiv', 'Mod': 'mod',
  'Eq': 'equal',  'NotEq': 'different',
  'Gt': 'greater', 'GtE': 'greater_eq', 'Lt': 'smaller', 'LtE': 'smaller_eq',
  'USub': 'minus', 'Not': 'not',
}


def parse_expression(state, expr):
  u.require_expr(expr)
  expr_type = u.node_type(expr)

  if expr_type == 'Name':
    hit = state.find_variable_id(expr, expr.id, u.node_type(expr.ctx) != 'Store')
    if hit:
      return p.variable_expression(hit['uuid'], hit['type'])
    if expr.id in BUILT_IN_VARIABLES:
      return p.builtin_variable_expression(expr.id, BUILT_IN_VARIABLES[expr.id])
    raise u.MissingNameError(expr.id)

  elif expr_type == 'Call':
    u.require_type(expr.func, 'Name')
    hit = state.find_function_id(expr.func, expr.func.id, True)
    args = [parse_expression(state, a) for a in expr.args]
    if hit:
      return p.call_expression(hit['uuid'], hit['type'], args)
    if expr.func.id in BUILT_IN_FUNCTIONS:
      if expr.func.id == 'len':
        if len(expr.args) != 1:
          u.parse_error(expr, 'Expected exactly one argument')
        return p.array_length_expression(args[0])
      else:
        # TODO determine possible types for builtins
        return p.call_builtin_expression(expr.func.id, 'unknown', args)
    raise u.MissingNameError(expr.func.id)

  elif expr_type == 'NameConstant':
    if expr.value is None:
      return p.literal_expression('unknown', None)
    if type(expr.value) == bool:
      return p.literal_expression('boolean', expr.value)
    else:
      u.unsupported_error(expr, "literal '{}'".format(expr.value))

  elif expr_type == 'Num':
    if type(expr.n) == int:
      return p.literal_expression('int', expr.n)
    return p.literal_expression('double', expr.n)

  elif expr_type == 'Str':
    return p.literal_expression('string', expr.s)

  elif expr_type == 'BinOp':
    op = u.node_type(expr.op)
    if op in OP_TABLE:
      left = parse_expression(state, expr.left)
      right = parse_expression(state, expr.right)
      if left['type'] == 'string' or right['type'] == 'string':
        typ = 'string'
      elif op == 'Div' or left['type'] == 'double' or right['type'] == 'double':
        typ = 'double'
      elif left['type'] == 'int' or right['type'] == 'int':
        typ = 'int'
      else:
        typ = 'unknown'
      return p.binary_operation(OP_TABLE[op], left, right, typ)
    u.unsupported_error(expr, "operation '{}'".format(op))

  elif expr_type == 'UnaryOp':
    op = u.node_type(expr.op)
    if op in OP_TABLE:
      operand = parse_expression(state, expr.operand)
      return p.unary_operation(OP_TABLE[op], operand, operand['type'])
    raise u.unsupported_error(expr, "operation '{}'".format(op))

  elif expr_type == 'BoolOp':
    op = u.node_type(expr.op)
    if op in OP_TABLE:
      args = [parse_expression(state, e) for e in expr.values]
      return build_bool_tree(op, args)

  elif expr_type == 'Compare':
    left = parse_expression(state, expr.left)
    args = [parse_expression(state, e) for e in expr.comparators]
    return build_compare_tree(expr, left, expr.ops, args)

  elif expr_type == 'Subscript':
    u.require_type(expr.value, 'Name')
    value = parse_expression(state, expr.value)
    sub_type = u.node_type(expr.slice)
    if sub_type == 'Index':
      index = parse_expression(state, expr.slice.value)
      return p.array_element_expression(value, index, p.unarray_type(value['type']))
    elif sub_type == 'Slice':
      lower = parse_expression(state, expr.slice.lower) if expr.slice.lower else None
      upper = parse_expression(state, expr.slice.upper) if expr.slice.upper else None
      step = parse_expression(state, expr.slice.step) if expr.slice.step else None
      return p.call_builtin_expression('slice', value['type'], [lower, upper, step])
    u.unsupported_error(expr, "'{}' as subscript".format(sub_type))

  elif expr_type in ('List', 'Tuple'):
    args = [parse_expression(state, e) for e in expr.elts]
    typ = u.common_type(expr, (a['type'] for a in args), 'multiple types in an array')
    return p.literal_expression(p.array_type(typ), args)

  elif not expr_type in IGNORE_NODES:
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
    return p.binary_operation(OP_TABLE[op], vals[0], build_bool_tree(op, vals[1:]), 'boolean')
  return p.binary_operation(OP_TABLE[op], vals[0], vals[1], 'boolean')

def build_compare_tree(expr, left, ops, comparators):
  op = u.node_type(ops[0])
  if op in OP_TABLE:
    cmp = p.binary_operation(OP_TABLE[op], left, comparators[0], 'boolean')
    if len(ops) > 1:
      return p.binary_operation(
        OP_TABLE['And'],
        cmp,
        build_compare_tree(expr, comparators[0], ops[1:], comparators[1:]),
        'boolean'
      )
    return cmp
  u.unsupported_error(expr, "operation '{}'".format(op))
