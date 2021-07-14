from . import parse_utils as u
from . import presentation as p

class ParseState:

  def __init__(self):
    self.constants = []
    self.procedures = []
    self.namestack = [{}]

  def add_procedure(self, id, type, parameters):
    procedure = p.procedure_declaration(u.uuid(), id, type, parameters)
    self.procedures.append(procedure)
    if id != None:
      self.namestack[-1][id] = procedure
    return procedure

  def push_names(self):
    self.namestack.append({})
  
  def pop_names(self):
    self.namestack.pop()

  def add_variable(self, id, type):
    variable = p.variable_statement(u.uuid(), id, type)
    self.namestack[-1][id] = variable
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
  
  def find_function_id(self, node, id, up=False):
    declaration = self.find_id(id, up)
    if declaration and not 'body' in declaration:
      u.parse_error(node, "Expected function id, got variable id '{}".format(id))
    return declaration
