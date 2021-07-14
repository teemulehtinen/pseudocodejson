import ast
import uuid as makeuuid

def node_type(node):
  return node.__class__.__name__

def node_line(node):
  return node.lineno if hasattr(node, 'lineno') else 0

def as_list(value):
  return value if isinstance(value, list) else [value]

def parse_error(node, error):
  raise ParseError("{} at line {:d}".format(error, node_line(node)))

def unsupported_error(node, unsupported_feature=None):
  raise ParseUnsupportedError("Unsupported {} at line {:d}".format(
    unsupported_feature if unsupported_feature else "'{}'".format(node_type(node)),
    node_line(node)
  ))

def require_type(node, accept):
  type = node_type(node)
  if not type in as_list(accept):
    parse_error(node, "Expected '{}' type, got '{}'".format("'/'".join(as_list(accept)), type))

def require_stmt(node):
  if not isinstance(node, ast.stmt):
    parse_error(node, "Expected statement, got '{}'".format(node_type(node)))

def require_expr(node):
  if not isinstance(node, ast.expr):
    parse_error(node, "Expected expression, got '{}'".format(node_type(node)))

def print_node(node):
  print(node_line(node), node_type(node), node._fields)

def print_tree(node):
  print(ast.dump(node))

def uuid():
  return str(makeuuid.uuid4())

class ParseError(Exception):
  pass

class ParseUnsupportedError(Exception):
  pass

class MissingNameError(Exception):
  def __init__(self, id):
    super().__init__("Missing name '{}'".format(id))
    self.id = id
