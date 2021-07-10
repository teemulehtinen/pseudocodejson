from . import parse_utils as u

class ParseState:

  def __init__(self):
    self.constants = []
    self.procedures = []
    self.namestack = [{}]

  def add_procedure(self, id, type, parameters):
    procedure = {
      'uuid': u.uuid(),
      'id': id,
      'type': type,
      'parameters': parameters,
      'body': [],
    }
    self.procedures.append(procedure)
    if id != None:
      self.namestack[-1][id] = procedure
    return procedure

  def push_names(self):
    self.namestack.append({})
  
  def pop_names(self):
    self.namestack.pop()

  def add_variable(self, id, type):
    variable = {
      'uuid': u.uuid(),
      'id': id,
      'type': type,
      'array': False
    }
    self.namestack[-1][id] = variable
    return variable

  def find_id(self, id):
    def find_recursion(self, id, level):
      if id in self.namestack[level]:
        return id
      return find_recursion(id, level - 1) if level > 0 else None
    return find_recursion(id, len(self.namestack) - 1)
