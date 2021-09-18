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
  '__name__': 'string', 'int': 'type', 'float': 'type', 'str': 'type'
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
    func_type = u.node_type(expr.func)
    args = [parse_expression(state, a) for a in expr.args]
    if func_type == 'Attribute':
      val = parse_expression(state, expr.func.value)
      if val['Expression'] == 'Literal':
        u.unsupported_error(expr.func, "method call '{}.{}'".format(val['type'], expr.func.attr))
      elif val['Expression'] == 'Variable':
        if p.is_array_type(val['type']) and expr.func.attr == 'append':
          return p.call_builtin_expression('array_grow', val['type'], [val['variable']] + args)
        u.unsupported_error(expr.func, "method call '{}.{}'".format(expr.func.value.id, expr.func.attr))
      # TODO math.floor etc support?
    elif func_type == 'Name':
      hit = state.find_function_id(expr.func, expr.func.id, True)
      if hit:
        return p.call_expression(hit['uuid'], hit['type'], args)
      elif expr.func.id in BUILT_IN_FUNCTIONS:
        if expr.func.id == 'len':
          if len(expr.args) != 1:
            u.parse_error(expr, 'Expected exactly one argument')
          return p.array_length_expression(args[0])
        # TODO elif expr.func.id == 'int'
        # TODO elif expr.func.id == 'round'
        # TODO elif expr.func.id == 'abs'
        else:
          # TODO determine possible types for builtins
          return p.call_builtin_expression(expr.func.id, 'unknown', args)
      raise u.MissingNameError(expr.func.id)
    else:
      u.unsupported_error(expr.func, "call of '{}'".format(func_type))

  elif expr_type == 'Constant':
    if expr.value is None:
      return p.null_expression()
    elif type(expr.value) == bool:
      return p.literal_expression('boolean', expr.value)
    elif type(expr.value) == int:
      return p.literal_expression('int', expr.value)
    elif type(expr.value) == float:
      return p.literal_expression('double', expr.value)
    elif type(expr.value) == str:
      return p.literal_expression('string', expr.value)
    else:
      u.unsupported_error(expr, "constant '{}'".format(expr.value))

  elif expr_type == 'NameConstant': # deprecated
    if expr.value is None:
      return p.null_expression()
    if type(expr.value) == bool:
      return p.literal_expression('boolean', expr.value)
    else:
      u.unsupported_error(expr, "literal '{}'".format(expr.value))

  elif expr_type == 'Num': # deprecated
    if type(expr.n) == int:
      return p.literal_expression('int', expr.n)
    return p.literal_expression('double', expr.n)

  elif expr_type == 'Str': # deprecated
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

  # TODO elif expr_type == 'IfExp':

  elif expr_type == 'Subscript':
    u.require_type(expr.value, 'Name')
    value = parse_expression(state, expr.value)
    sub_type = u.node_type(expr.slice)
    if sub_type == 'Slice':
      u.unsupported_error(expr, 'creation of a slice from an iterable')
    else:
      index = parse_expression(state, expr.slice.value if sub_type == 'Index' else expr.slice)
      return p.array_element_expression(value, index, p.unarray_type(value['type']))

  elif expr_type in ('List', 'Tuple'):
    # TODO should allocate and populate
    u.unsupported_error(expr)

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
