import unittest
import json
from pseudocodejson import src2json

class TestSamples(unittest.TestCase):

  def test_function(self):
    pseudo = src2json(
"""
def sample(a):
  return 2*a
    
#sample(2)
""")
    print(json.dumps(pseudo, indent=2))

  def test_bubblesort(self):
    pseudo = src2json(
"""
def bubblesort(a):
  changes = True
  while changes:
    changes = False
    for i in range(1, len(a)):
      if a[i] < a[i - 1]:
        #a[i], a[i - 1] = a[i - 1], a[i]
        a[i] = a[i - 1]
        a[i - 1] = a[i]
        changes = True
  return a
"""
    )
    print(json.dumps(pseudo, indent=2))
