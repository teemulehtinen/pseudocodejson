def procedure_declaration(uuid, id, type):
  return {
    'Statement': 'Procedure',
    'uuid': uuid,
    'id': id,
    'type': type,
    'parameters': [],
    'body': [],
    '_children': ['parameters', 'body'],
  }

def variable_statement(uuid, id, type):
  return {
    'Statement': 'Variable',
    'uuid': uuid,
    'id': id,
    'type': type,
  }

def call_statement(uuid, args):
  return {
    'Statement': 'Call',
    'procedure': uuid,
    'arguments': args,
    '_children': ['arguments'],
  }

def return_statement(expression, typ):
  return {
    'Statement': 'Return',
    'expression': expression,
    'type': typ,
    '_children': ['expression'],
  }

def assignment_statement(uuid, expression):
  return {
    'Statement': 'Assignment',
    'variable': uuid,
    'expression': expression,
    '_children': ['expression'],
  }

def array_assignment_statement(target, indexes, expression):
  return {
    'Statement': 'Array Assignment',
    'target': target,
    'indexes': indexes,
    'expression': expression,
    '_children': ['target', 'indexes', 'expression'],
  }

def selection_statement(guard, body, alternative):
  return {
    'Statement': 'Selection',
    'guard': guard,
    'body': body,
    'alternative': alternative,
    '_children': ['guard', 'body', 'alternative'],
  }

def loop_statement(guard, body):
  return {
    'Statement': 'Loop',
    'guard': guard,
    'body': body,
    '_children': ['guard', 'body'],
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
    '_children': ['call'],
  }

def call_builtin_expression(id, typ, args):
  return {
    'Expression': 'Call',
    'builtin': id,
    'arguments': args,
    'type': typ,
    '_children': ['arguments'],
  }

def array_length_expression(target):
  return {
    'Expression': 'Array Length',
    'target': target,
    'indexes': [],
    'type': 'int',
    '_children': ['target', 'indexes'],
  }

def array_element_expression(target, index, typ):
  return {
    'Expression': 'Array Element',
    'target': target,
    'indexes': [index],
    'type': typ,
    '_children': ['target', 'indexes'],
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
    '_children': ['left', 'right'],
  }

def unary_operation(op, expression, typ):
  return {
    'Expression': 'Unary Op',
    'op': op,
    'expression': expression,
    'type': typ,
    '_children': ['expression'],
  }

def array_type(typ):
  return typ + '[]'

def is_array_type(typ):
  return typ.endswith('[]')

def unarray_type(typ):
  if is_array_type(typ):
    return typ[:-2]
  return 'unknown'

def should_have_type(e):
  return (
    e.get('Statement') in ('Procedure', 'Variable')
    or e.get('Expression') in ('Literal',)
  )

def finalize(statements):
  def filter(s):
    sp = { k: v for k, v in s.items() if not k in ('type', '_children') }
    if should_have_type(s):
      typ = s.get('type', 'unknown')
      if is_array_type(typ):
        sp['type'] = unarray_type(typ)
        sp['array'] = True
      else:
        sp['type'] = typ
        sp['array'] = False
    for c in s.get('_children', []):
      sp[c] = finalize(s[c])
    return sp
  if type(statements) == list:
    return [filter(s) for s in statements]
  return filter(statements)
