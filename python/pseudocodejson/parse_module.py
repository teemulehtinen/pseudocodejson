from .parse_statements import parse_statements
from .ParseState import ParseState
from . import parse_utils as u

def parse_module(module):
  u.require_type(module, 'Module')

  state = ParseState()
  module_stmt, _ = parse_statements(state, module.body)
  if (len(module_stmt) > 0):
    default = state.add_procedure(None, 'void')
    default['body'].extend(module_stmt)

  return {
    'type': 'Module',
    'id': None,
    'constants': state.constants,
    'procedures': state.procedures,
  }

# mod = Module(stmt* body, type_ignore* type_ignores)
#   | Interactive(stmt* body)
#   | Expression(expr body)
#   | FunctionType(expr* argtypes, expr returns)
