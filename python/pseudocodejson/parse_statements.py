from . import parse_utils as u
from . import presentation as p
from .parse_expression import parse_expression, OP_TABLE

IGNORE_NODES = ['Delete', 'Import', 'ImportFrom', 'Assert']
IGNORE_BUILTINS = ['print']
DEFAULT_TYPE = 'unknown'

def parse_statements(state, stmt):
  json = []
  function_defs = []

  for s in stmt:
    u.require_stmt(s)
    stmt_type = u.node_type(s)

    if stmt_type == 'FunctionDef':
      function_defs.append([
        state.add_procedure(s.name, DEFAULT_TYPE, parse_args(state, s.args)),
        s.body
      ])

    elif stmt_type == 'Return':
      json.append(p.return_statement(parse_expression(state, s.value) if s.value else None))

    elif stmt_type == 'Assign':
      value_exp = parse_expression(state, s.value)
      for target in s.targets:
        parse_assignment_target(state, json, s, target, value_exp)
    
    elif stmt_type == 'AugAssign':
      op = u.node_type(s.op)
      if op in OP_TABLE:
        value_exp = p.binary_operation(
          OP_TABLE[op],
          parse_expression(state, s.target),
          parse_expression(state, s.value)
        )
        if not add_array_assignment(state, json, s.target, value_exp):
          json.append(p.assignment_statement(parse_target_uuid(state, s.target), value_exp))
      else:
        u.unsupported_error(s, "operation '{}'".format(op))

    elif stmt_type == 'If':
      json.append(p.selection_statement(
        parse_expression(state, s.test),
        parse_statements(state, s.body),
        parse_statements(state, s.orelse)
      ))

    elif stmt_type == 'While':
      if len(s.orelse) > 0:
        u.unsupported_error(s, "else-block in 'While'")
      json.append(p.loop_statement(
        parse_expression(state, s.test),
        parse_statements(state, s.body)
      ))
    
    elif stmt_type == 'For':
      if len(s.orelse) > 0:
        u.unsupported_error(s, "else-block in 'For'")
      uuid = parse_or_create_target_uuid(state, json, s.target)
      iter = parse_expression(state, s.iter)
      if iter['Expression'] == 'Call' and iter['builtin'] == 'range':
        args = iter['arguments']
        json.append(p.assignment_statement(
          uuid,
          args[0] if len(args) > 1 else p.literal_expression('int', 0)
        ))
        json.append(p.loop_statement(
          p.binary_operation(
            'different',
            p.variable_expression(uuid),
            args[1 if len(args) > 1 else 0]
          ),
          parse_statements(state, s.body) + [p.assignment_statement(
            uuid,
            p.binary_operation(
              'add',
              p.variable_expression(uuid),
              args[2] if len(args) > 2 else p.literal_expression('int', 1)
            )
          )]
        ))
      else:
        u.unsupported_error(s, "for (only 'in range' is supported)")

    elif stmt_type == 'Expr':
      e = parse_expression(state, s.value)
      if e['Expression'] == 'Call':
        if 'call' in e:
          json.append(e['call'])
        elif not e['builtin'] in IGNORE_BUILTINS:
          u.unsupported_error(s, "builtin function '{}'".format(e['builtin']))
      elif e['Expression'] == 'Literal' and e['type'] == 'string':
        pass # Skip comment
      else:
        u.unsupported_error(s, "expression '{}' as statement".format(e['Expression']))

    elif not stmt_type in IGNORE_NODES:
      u.unsupported_error(s)
  
  # Python naming is single-pass when function bodies are parsed after parent.
  for fdef,fstmt in function_defs:
    state.push_names()
    fdef['body'].extend(parse_statements(state, fstmt))
    state.pop_names()

  return json

# stmt = FunctionDef(identifier name, arguments args, stmt* body, expr* decorator_list, expr? returns, string? type_comment)
#   | AsyncFunctionDef(identifier name, arguments args, stmt* body, expr* decorator_list, expr? returns, string? type_comment)
#   | ClassDef(identifier name, expr* bases, keyword* keywords, stmt* body, expr* decorator_list)
#   | Return(expr? value)
#
#   | Delete(expr* targets)
#   | Assign(expr* targets, expr value, string? type_comment)
#   | AugAssign(expr target, operator op, expr value)
#   | AnnAssign(expr target, expr annotation, expr? value, int simple)
#
#   | For(expr target, expr iter, stmt* body, stmt* orelse, string? type_comment)
#   | AsyncFor(expr target, expr iter, stmt* body, stmt* orelse, string? type_comment)
#   | While(expr test, stmt* body, stmt* orelse)
#   | If(expr test, stmt* body, stmt* orelse)
#   | With(withitem* items, stmt* body, string? type_comment)
#   | AsyncWith(withitem* items, stmt* body, string? type_comment)
#
#   | Raise(expr? exc, expr? cause)
#   | Try(stmt* body, excepthandler* handlers, stmt* orelse, stmt* finalbody)
#   | Assert(expr test, expr? msg)
#
#   | Import(alias* names)
#   | ImportFrom(identifier? module, alias* names, int? level)
#
#   | Global(identifier* names)
#   | Nonlocal(identifier* names)
#   | Expr(expr value)
#   | Pass | Break | Continue

def parse_args(state, args):
  return [state.add_variable(a.arg, DEFAULT_TYPE) for a in args.args]

# arguments = (arg* posonlyargs, arg* args, arg? vararg, arg* kwonlyargs, expr* kw_defaults, arg? kwarg, expr* defaults)
# arg = (identifier arg, expr? annotation, string? type_comment)

def parse_assignment_target(state, json, stmt, target, value_exp):
  if u.node_type(target) in ('Tuple', 'List'):
    if value_exp['Expression'] != 'Literal' or value_exp['type'] != 'array':
      u.unsupported_error(stmt, 'assignment of {} to tuple'.format(value_exp['Expression']))
    target_n = len(target.elts)
    value_n = len(value_exp['value'])
    if target_n != value_n:
      u.unsupported_error(stmt, 'assignment of length {} to tuple of length {}'.format(value_n, target_n))
    for i in range(target_n):
      parse_assignment_target(state, json, stmt, target.elts[i], value_exp['value'][i])
  elif not add_array_assignment(state, json, target, value_exp):
    uuid = parse_or_create_target_uuid(state, json, target)
    json.append(p.assignment_statement(uuid, value_exp))

def add_array_assignment(state, json, target, value_exp):
  if u.node_type(target) == 'Subscript':
    arr = parse_expression(state, target)
    json.append(p.array_assignment_statement(arr['target'], arr['indexes'], value_exp))
    return True
  return False

def parse_target_uuid(state, target):
  u.require_type(target, 'Name')
  return parse_expression(state, target)['variable']

def parse_or_create_target_uuid(state, json, target):
  try:
    return parse_target_uuid(state, target)
  except u.MissingNameError as error:
    declaration = state.add_variable(error.id, DEFAULT_TYPE)
    json.append(declaration)
    return declaration['uuid']
