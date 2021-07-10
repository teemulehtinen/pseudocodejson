import ast
import uuid as makeuuid

def node_type(node):
  return node.__class__.__name__

def node_line(node):
  return node.lineno if hasattr(node, 'lineno') else 0

def as_list(value):
  return value if isinstance(value, list) else [value]

def require_type(type, accept):
  if not type in as_list(accept):
    raise ParseError("Expected '{}' type, got '{}'".format(
      as_list(accept).join("'/'"),
      type)
    )

def require_stmt(node):
  if not isinstance(node, ast.stmt):
    raise ParseError("Expected statement, got '{}' at line {:d}".format(
      node_type(node),
      node_line(node)
    ))

def require_expr(node):
  if not isinstance(node, ast.expr):
    raise ParseError("Expected expression, got '{}' at line {:d}".format(
      node_type(node),
      node_line(node)
    ))

def unsupported_error(node):
  raise ParseUnsupportedError("Unsupported '{}' at line {:d}".format(
    node_type(node),
    node_line(node)
  ))

def print_node(node):
  print(node_line(node), node_type(node), node._fields)

def print_tree(node):
  print(ast.dump(node))

def uuid():
  return makeuuid.uuid4()

class ParseError(Exception):
  pass

class ParseUnsupportedError(Exception):
  pass
