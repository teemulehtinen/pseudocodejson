import ast
import json
from .parse_module import parse_module
from .parse_statements import parse_statements
from .parse_expression import parse_expression

VERSION_STRING = "1.0.0"

def src2pseudo(src):
  root = ast.parse(src)
  return {
    "format": "pseudocodejson",
    "version": VERSION_STRING,
    **parse_module(root)
  }

def srcfile2pseudo(filename):
  with open(filename) as f:
    src = f.read()
  return src2pseudo(src)
