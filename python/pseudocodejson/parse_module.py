from .parse_statements import parse_statements
from .ParseState import ParseState
from . import presentation as p
from . import parse_utils as u

def parse_module(module, typed_signatures=None, exlude_procedures=None, fail_nodes=None):
  u.require_type(module, 'Module')

  state = ParseState(typed_signatures, exlude_procedures, fail_nodes)
  module_stmt, _ = parse_statements(state, module.body)
  if (len(module_stmt) > 0):
    default = state.add_procedure(None, 'void')
    default['body'].extend(module_stmt)

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
