from . import parse_utils as u
from . import presentation as p
from .parse_expression import parse_expression

IGNORE_NODES = ['Delete', 'Import', 'ImportFrom', 'Assert']
DEFAULT_TYPE = 'unknown'

def parse_statements(state, stmt):
  json = []
  function_defs = []

  for s in stmt:
    u.require_stmt(s)
    type = u.node_type(s)

    if type == 'FunctionDef':
      function_defs.append([
        state.add_procedure(s.name, DEFAULT_TYPE, parse_args(state, s.args)),
        s.body
      ])

    elif type == 'Return':
      json.append(p.return_statement(parse_expression(state, s.value) if s.value else None))

    elif type == 'Assign':
      value_exp = parse_expression(state, s.value)
      if len(s.targets) > 1:
        #u.print_tree(s)
        # TODO test and unpack value to separate assignments
        u.unsupported_error(s, 'unpacking assignment')
      for target in s.targets:
        type = u.node_type(target)
        if type == 'Subscript':
          expr = parse_expression(state, target)
          json.append(p.array_assignment_statement(
            expr['target']['variable'],
            expr['indexes'],
            value_exp
          ))
        else:
          uuid = parse_target_uuid(state, json, target)
          json.append(p.assignment_statement(uuid, value_exp))

    elif type == 'If':
      json.append(p.selection_statement(
        parse_expression(state, s.test),
        parse_statements(state, s.body),
        parse_statements(state, s.orelse)
      ))

    elif type == 'While':
      if len(s.orelse) > 0:
        u.unsupported_error(s, "else-block in 'While'")
      json.append(p.loop_statement(
        parse_expression(state, s.test),
        parse_statements(state, s.body)
      ))
    
    elif type == 'For':
      if len(s.orelse) > 0:
        u.unsupported_error(s, "else-block in 'For'")
      uuid = parse_target_uuid(state, json, s.target)
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
              'sum',
              p.variable_expression(uuid),
              args[2] if len(args) > 2 else p.literal_expression('int', 1)
            )
          )]
        ))
      else:
        u.unsupported_error(s, "for (only 'in range' is supported)")

    elif type == 'Expr':
      e = parse_expression(s.value)
      if e['Expression'] != 'Call':
        u.unsupported_error(s, "expression statement (only 'Call' is supported)")
      if 'call' in e:
        json.append(e['call'])
      else:
        u.unsupported_error(s, "builtin function '{}'".format(e['builtin']))

    elif not type in IGNORE_NODES:
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

def parse_target_uuid(state, json, target):
  u.require_type(target, 'Name')
  try:
    return parse_expression(state, target)['variable']
  except u.MissingNameError as error:
    declaration = state.add_variable(error.id, DEFAULT_TYPE)
    json.append(declaration)
    return declaration['uuid']
