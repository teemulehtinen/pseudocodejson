from .parse_statements import parse_statements
from .ParseState import ParseState
from . import presentation as p
from . import parse_utils as u

def parse_module(module, typed_signatures=None, exclude_others=False):
  u.require_type(module, 'Module')

  state = ParseState(typed_signatures)
  module_stmt, module_typ = parse_statements(state, module.body, exclude_others, True)
  if (len(module_stmt) > 0):
    default = state.add_procedure(True, None, None, None, module_typ)
    default['parameters'] = []
    default['body'] = module_stmt

  return {
    'type': 'Module',
    'id': None,
    'constants': p.finalize(state.constants),
    'procedures': p.finalize(state.procedures),
  }

# mod = Module(stmt* body, type_ignore* type_ignores)
#   | Interactive(stmt* body)
#   | Expression(expr body)
#   | FunctionType(expr* argtypes, expr returns)
