def procedure_declaration(uuid, id, type, parameters):
  return {
    'uuid': uuid,
    'id': id,
    'type': type,
    'parameters': parameters,
    'body': [],
  }

def variable_statement(uuid, id, type):
  return {
    'Statement': 'Variable',
    'uuid': uuid,
    'id': id,
    'type': type,
    #'array': false,
  }

def call_statement(uuid, args):
  return {
    'Statement': 'Call',
    'procedure': uuid,
    'arguments': args,
  }

def return_statement(expression=None):
  return {
    'Statement': 'Return',
    'expression': expression,
  }

def assignment_statement(uuid, expression):
  return {
    'Statement': 'Assignment',
    'variable': uuid,
    'expression': expression,
  }

def selection_statement(guard, body, alternative):
  return {
    'Statement': 'Selection',
    'guard': guard,
    'body': body,
    'alternative': alternative,
  }

def loop_statement(guard, body):
  return {
    'Statement': 'Loop',
    'guard': guard,
    'body': body,
  }

def array_assignment_statement(target, indexes, expression):
  return {
    'Statement': 'Array Assignment',
    'target': target,
    'indexes': indexes,
    'expression': expression,
  }

def variable_expression(uuid):
  return {
    'Expression': 'Variable',
    'variable': uuid,
  }

def builtin_variable_expression(id):
  return {
    'Expression': 'Variable',
    'builtin': id,
  }

def call_expression(uuid, args):
  return {
    'Expression': 'Call',
    'call': call_statement(uuid, args),
  }

def call_builtin_expression(id, args):
  return {
    'Expression': 'Call',
    'builtin': id,
    'arguments': args,
  }

def array_length_expression(target):
  return {
    'Expression': 'Array Length',
    'target': target,
    'indexes': [],
  }

def array_element_expression(target, index):
  return {
    'Expression': 'Array Element',
    'target': target,
    'indexes': [index]
  }

def literal_expression(type, value):
  return {
    'Expression': 'Literal',
    'type': type,
    'value': value,
  }

def binary_operation(op, left, right):
  return {
    'Expression': 'Binary Op',
    'op': op,
    'left': left,
    'right': right,
  }

def unary_operation(op, expression):
  return {
    'Expression': 'Unary Op',
    'op': op,
    'expression': expression,
  }
