import unittest
import json
from pseudocodejson import src2pseudo

class TestSamples(unittest.TestCase):

  def test_function(self):
    pseudo = src2pseudo(
"""
def sample(a):
  return 2*a
    
sample(2)
""")
    print(json.dumps(pseudo, indent=2))

  def test_bubblesort(self):
    pseudo = src2pseudo(
"""
def bubblesort(a):
  changes = True
  while changes:
    changes = False
    for i in range(1, len(a)):
      if a[i] < a[i - 1]:
        a[i], a[i - 1] = a[i - 1], a[i]
        changes = True
  return a
"""
    )
    print(json.dumps(pseudo, indent=2))

  def test_extended(self):
    pseudo = src2pseudo(
"""
a = b = None
a = 0
b = 10
while True and 0 <= a <= b:
  a += 1
"""
    )
    print(json.dumps(pseudo, indent=2))

  def test_ignored(self):
    pseudo = src2pseudo(
"""
a = 3
b = a // 2
print("blaa")
"""
    )
    print(json.dumps(pseudo, indent=2))
