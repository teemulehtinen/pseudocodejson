from . import parse_utils as u
from . import presentation as p

class ParseState:

  def __init__(self, typed_signatures=None):
    self.constants = []
    self.procedures = []
    self.namestack = [{}]
    self.variable_typing = {}
    self.typed_signatures = typed_signatures or {}

  def add_procedure(self, module_root, id, typ=None):
    if module_root and id in self.typed_signatures:
      styp = self.typed_signatures[id]['return']
      called = True
    else:
      styp = 'unknown'
      called = False
    procedure = p.procedure_declaration(u.uuid(), id, typ or styp, called)
    self.procedures.append(procedure)
    self.namestack[-1][id] = procedure
    return procedure

  def push_names(self):
    self.namestack.append({})
  
  def pop_names(self):
    self.namestack.pop()

  def add_variable(self, id, typ=None, func_id=None, func_arg_i=0):
    if typ is None:
      if func_id and func_id in self.typed_signatures:
        arg_def = self.typed_signatures[func_id]['arguments']
        if func_arg_i < len(arg_def) and arg_def[func_arg_i][0] in (None, id):
          typ = arg_def[func_arg_i][1]
        else:
          typ = 'unknown'
      else:
        typ = 'unknown'
    variable = p.variable_statement(u.uuid(), id, typ)
    self.namestack[-1][id] = variable
    self.variable_typing[variable['uuid']] = typ
    return variable
  
  def find_id(self, id, up=False, level=None):
    if level is None:
      level = len(self.namestack) - 1
    if id in self.namestack[level]:
      return self.namestack[level][id]
    if up and level > 0:
      return self.find_id(id, True, level - 1)
    return None
  
  def find_variable_id(self, node, id, up=False):
    declaration = self.find_id(id, up)
    if declaration and 'body' in declaration:
      u.parse_error(node, "Expected variable id, got function id '{}'".format(id))
    return declaration
  
  def find_function_id(self, node, id, args):
    declaration = self.find_id(id, True)
    if declaration:
      declaration['_called'] = True
      if not 'body' in declaration:
        u.parse_error(node, "Expected function id, got variable id '{}".format(id))
      if not id in self.typed_signatures:
        self.typed_signatures[id] = {
          'return': 'unknown',
          'arguments': [(None, a.get('type', 'unknown')) for a in args],
        }
    return declaration

  def set_variable_type(self, node, uuid, typ):
    if typ != 'unknown':
      if not self.variable_typing.get(uuid, 'unknown') in (typ, 'unknown'):
        u.unsupported_error(node, "multiple types for a variable")
      self.variable_typing[uuid] = typ
  
  def get_variable_type(self, uuid):
    return self.variable_typing.get(uuid, 'unknown')

  def get_required_to_parse(self):
    return [
      f['uuid'] for f in self.namestack[-1].values()
      if 'body' in f and f['body'] is None and f['_called']
    ]
