import sys
import json
from . import srcfile2pseudo

if not len(sys.argv) in (2, 3):
  print("Transposes simple python programs into pseudocodejson")
  print("Usage: pseudocodejson python_source_file [procedure_id]")
else:
  if len(sys.argv) == 3:
    signatures = { sys.argv[2]: { 'return': 'unknown', 'arguments': [] } }
    exclude = True
  else:
    signatures = None
    exclude = False
  print(json.dumps(srcfile2pseudo(sys.argv[1], signatures, exclude), indent=2))
