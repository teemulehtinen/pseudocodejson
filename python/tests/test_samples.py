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

  def test_mergesort(self):
    pseudo = src2pseudo(
"""
def shift_selection_to_right(a, beg, end):
  for i in range(end, beg, -1):
    a[i] = a[i - 1]

def merge_sort_in_place(a, beg, end):
  # Implement merge sort without using new lists
  n = end - beg
  if n > 1:
    pivot = beg + n // 2
    merge_sort_in_place(a, beg, pivot)
    merge_sort_in_place(a, pivot, end)
    left = beg
    right = pivot
    while left < pivot and right < end:
      if a[left] <= a[right]:
        left += 1
      else:
        t = a[right]
        shift_selection_to_right(a, left, right)
        a[left] = t
        left += 1
        pivot += 1
        right += 1
""",
      {
        'shift_selection_to_right': {
          'return': 'void',
          'arguments': [
            ('a', 'int[]'),
            ('beg', 'int'),
            ('end', 'int'),
          ],
        },
        'merge_sort_in_place': {
          'return': 'void',
          'arguments': [
            ('a', 'int[]'),
            ('beg', 'int'),
            ('end', 'int'),
          ],
        },
      }
    )
    print(json.dumps(pseudo, indent=2))
