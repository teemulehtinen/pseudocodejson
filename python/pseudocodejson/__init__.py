import ast
import json
from .parse_module import parse_module
from .parse_statements import parse_statements
from .parse_expression import parse_expression
from .parse_utils import ParseError, ParseUnsupportedError, MissingNameError

VERSION_STRING = "1.0.0"

def src2pseudo(src, typed_signatures=None, exclude_others=False):
  root = ast.parse(src)
  return {
    "format": "pseudocodejson",
    "version": VERSION_STRING,
    **parse_module(root, typed_signatures, exclude_others)
  }

def srcfile2pseudo(filename, typed_signatures=None, exclude_others=False):
  with open(filename) as f:
    src = f.read()
  return src2pseudo(src, typed_signatures, exclude_others)
