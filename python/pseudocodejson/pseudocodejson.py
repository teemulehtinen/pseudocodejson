import ast
import json
from .parse_module import parse_module

VERSION_STRING = "1.0.0"

def src2json(src):
  root = ast.parse(src)
  return {
    "format": "pseudocodejson",
    "version": VERSION_STRING,
    **parse_module(root)
  }

def srcfile2json(filename):
  with open(filename) as f:
    src = f.read()
  return src2json(src)

if __name__ == '__main__':
  import sys
  if len(sys.argv) != 2:
    print("Transposes simple python programs into pseudocodejson")
    print("Usage: {} [python_source_file]".format(sys.argv[0]))
  else:
    print(json.dumps(srcfile2json(sys.argv[1]), indent=2))
