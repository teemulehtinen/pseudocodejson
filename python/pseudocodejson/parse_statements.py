from . import parse_utils as u
from . import presentation as p
from .parse_expression import parse_expression, OP_TABLE

IGNORE_NODES = ['Pass', 'Delete', 'Import', 'ImportFrom', 'Assert', 'Raise']
IGNORE_BUILTINS = ['print']

def parse_statements(state, stmt):
  json = []
  return_types = []
  function_defs = []

  for s in stmt:
    u.require_stmt(s)
    stmt_type = u.node_type(s)

    if stmt_type == 'FunctionDef':
      function_defs.append([
        state.add_procedure(s.name, 'void'),
        s.args,
        s.body
      ])

    elif stmt_type == 'Return':
      value = parse_expression(state, s.value) if s.value else None
      typ = value['type'] if value else 'void'
      json.append(p.return_statement(value, typ))
      return_types.append(typ)

    elif stmt_type == 'Assign':
      value_exp = parse_expression(state, s.value)
      for target in s.targets:
        parse_assignment_target(state, json, s, target, value_exp)

    elif stmt_type == 'AugAssign':
      op = u.node_type(s.op)
      if op in OP_TABLE:
        val = parse_expression(state, s.value)
        value_exp = p.binary_operation(
          OP_TABLE[op],
          parse_expression(state, s.target),
          val,
          val['type']
        )
        if not add_array_assignment(state, json, s.target, value_exp):
          uuid = parse_target_uuid(state, s.target, value_exp['type'])
          json.append(p.assignment_statement(uuid, value_exp))
      else:
        u.unsupported_error(s, "operation '{}'".format(op))

    elif stmt_type == 'If':
      cond = parse_expression(state, s.test)
      if_body, if_typ = parse_statements(state, s.body)
      else_body, else_typ = parse_statements(state, s.orelse)
      json.append(p.selection_statement(cond, if_body, else_body))
      return_types.extend([if_typ, else_typ])

    elif stmt_type == 'While':
      if len(s.orelse) > 0:
        u.unsupported_error(s, "else-block in 'While'")
      cond = parse_expression(state, s.test)
      body, typ = parse_statements(state, s.body)
      json.append(p.loop_statement(cond, body))
      return_types.append(typ)

    elif stmt_type == 'For':
      if len(s.orelse) > 0:
        u.unsupported_error(s, "'Else' in 'For'")
      iter = parse_expression(state, s.iter)
      if iter['Expression'] == 'Call' and iter['builtin'] == 'range':
        uuid = parse_or_create_target_uuid(state, json, s.target, 'int')
        args = iter['arguments']
        begin = args[0] if len(args) > 1 else p.literal_expression('int', 0)
        end = args[1 if len(args) > 1 else 0]
        step = args[2] if len(args) > 2 else p.literal_expression('int', 1)
        body, typ = parse_statements(state, s.body)
        json.append(p.assignment_statement(uuid, begin))
        json.append(p.loop_statement(
          p.binary_operation('different', p.variable_expression(uuid, 'int'), end, 'boolean'),
          body + [
            p.assignment_statement(
              uuid,
              p.binary_operation('add', p.variable_expression(uuid, 'int'), step, 'int')
            )
          ]
        ))
      else:
        u.unsupported_error(s, "for iterable (only 'range' is supported)")

    elif stmt_type == 'Break':
      json.append(p.break_statement())
    
    elif stmt_type == 'Continue':
      json.append(p.continue_statement())

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
  for fdef, fargs, fstmt in function_defs:
    state.push_names()
    fdef['parameters'] = parse_args(state, fargs)
    body, typ = parse_statements(state, fstmt)
    fdef['body'].extend(body)
    fdef['type'] = typ
    state.pop_names()

  typ = u.common_type(stmt, return_types, 'multiple return types for a function')
  return json, typ

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
  return [state.add_variable(a.arg, 'unknown') for a in args.args]

# arguments = (arg* posonlyargs, arg* args, arg? vararg, arg* kwonlyargs, expr* kw_defaults, arg? kwarg, expr* defaults)
# arg = (identifier arg, expr? annotation, string? type_comment)

def parse_assignment_target(state, json, stmt, target, value_exp):
  if u.node_type(target) in ('Tuple', 'List'):
    if value_exp['Expression'] != 'Literal' or not p.is_array_type(value_exp['type']):
      u.unsupported_error(stmt, 'assignment of {} to tuple'.format(value_exp['Expression']))
    target_n = len(target.elts)
    value_n = len(value_exp['value'])
    if target_n != value_n:
      u.unsupported_error(stmt, 'assignment of length {} to tuple of length {}'.format(value_n, target_n))
    for i in range(target_n):
      # TODO fix with temporary variables
      parse_assignment_target(state, json, stmt, target.elts[i], value_exp['value'][i])
  elif not add_array_assignment(state, json, target, value_exp):
    uuid = parse_or_create_target_uuid(state, json, target, value_exp['type'])
    json.append(p.assignment_statement(uuid, value_exp))

def add_array_assignment(state, json, target, value_exp):
  if u.node_type(target) != 'Subscript':
    return False
  arr = parse_expression(state, target)
  if arr['Expression'] == 'Call':
    u.unsupported_error(target, 'assignment to array slice')
  if 'builtin' in arr['target']:
    u.unsupported_error(target, 'assignment to builtin')
  typ = p.array_type(value_exp['type'])
  state.set_variable_type(target, arr['target']['variable'], typ)
  arr['target']['type'] = typ
  json.append(p.array_assignment_statement(arr['target'], arr['indexes'], value_exp))
  return True

def parse_target_uuid(state, target, typ):
  u.require_type(target, 'Name')
  var = parse_expression(state, target)
  state.set_variable_type(target, var['variable'], typ)
  var['type'] = typ
  return var['variable']

def parse_or_create_target_uuid(state, json, target, typ):
  try:
    return parse_target_uuid(state, target, typ)
  except u.MissingNameError as error:
    var = state.add_variable(error.id, typ)
    json.append(var)
    return var['uuid']
