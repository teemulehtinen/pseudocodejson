import unittest
from pseudocodejson import src2json

class TestSamples(unittest.TestCase):

  def test_function(self):
    json = src2json(
"""
def sample(a):
  return 2*a
    
#sample(2)
""")
    print(json)
