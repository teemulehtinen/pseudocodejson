def procedure_declaration(uuid, id, type):
  return {
    'uuid': uuid,
    'id': id,
    'type': type,
    'parameters': [],
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

def return_statement(expression, typ):
  return {
    'Statement': 'Return',
    'expression': expression,
    'type': typ,
  }

def assignment_statement(uuid, expression):
  return {
    'Statement': 'Assignment',
    'variable': uuid,
    'expression': expression,
  }

def array_assignment_statement(target, indexes, expression):
  return {
    'Statement': 'Array Assignment',
    'target': target,
    'indexes': indexes,
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

def break_statement():
  return {
    'Statement': 'Break',
  }

def continue_statement():
  return {
    'Statement': 'Continue',
  }

def variable_expression(uuid, typ):
  return {
    'Expression': 'Variable',
    'variable': uuid,
    'type': typ,
  }

def builtin_variable_expression(id, typ):
  return {
    'Expression': 'Variable',
    'builtin': id,
    'type': typ,
  }

def call_expression(uuid, typ, args):
  return {
    'Expression': 'Call',
    'call': call_statement(uuid, args),
    'type': typ,
  }

def call_builtin_expression(id, typ, args):
  return {
    'Expression': 'Call',
    'builtin': id,
    'arguments': args,
    'type': typ,
  }

def array_length_expression(target):
  return {
    'Expression': 'Array Length',
    'target': target,
    'indexes': [],
    'type': 'int',
  }

def array_element_expression(target, index, typ):
  return {
    'Expression': 'Array Element',
    'target': target,
    'indexes': [index],
    'type': typ,
  }

def literal_expression(type, value):
  return {
    'Expression': 'Literal',
    'type': type,
    'value': value,
  }

def binary_operation(op, left, right, typ):
  return {
    'Expression': 'Binary Op',
    'op': op,
    'left': left,
    'right': right,
    'type': typ,
  }

def unary_operation(op, expression, typ):
  return {
    'Expression': 'Unary Op',
    'op': op,
    'expression': expression,
    'type': typ,
  }

def array_type(typ):
  return typ + '[]'

def is_array_type(typ):
  return typ.endswith('[]')

def unarray_type(typ):
  if is_array_type(typ):
    return typ[:-2]
  return 'unknown'
