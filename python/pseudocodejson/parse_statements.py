from . import parse_utils as u
from .parse_expression import parse_expression

IGNORE_NODES = ['Delete', 'Import', 'ImportFrom']
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
      json.append({
        'type': 'Return',
        'expression': parse_expression(s.value) if s.value else None,
      })

    #TODO if, assign, while, for

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
