import sys
import json
from . import srcfile2pseudo

if len(sys.argv) != 2:
  print("Transposes simple python programs into pseudocodejson")
  print("Usage: pseudocodejson [python_source_file]")
else:
  print(json.dumps(srcfile2pseudo(sys.argv[1]), indent=2))
