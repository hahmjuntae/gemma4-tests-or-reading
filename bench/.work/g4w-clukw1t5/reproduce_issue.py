import sys
import os

# Ensure we are using the bisect.py in /work
sys.path.insert(0, '/work')
import bisect

def test_bisect_right_with_key():
    a = [1, 2, 2, 3]
    key = lambda x: x
    x = 2
    # bisect_right should return 3 because there are two 2s, and it should be after them.
    # The target value passed to bisect_right is key(x) = 2.
    res = bisect.bisect_right(a, x, key=key)
    print(f"bisect_right([1, 2, 2, 3], 2, key=lambda x: x) = {res}")
    assert res == 3, f"Expected 3, got {res}"

def test_bisect_left_with_key():
    a = [1, 2, 2, 3]
    key = lambda x: x
    x = 2
    # bisect_left should return 1 because the first 2 is at index 1.
    res = bisect.bisect_left(a, x, key=key)
    print(f"bisect_left([1, 2, 2, 3], 2, key=lambda x: x) = {res}")
    assert res == 1, f"Expected 1, got {res}"

if __name__ == "__main__":
    try:
        test_bisect_right_with_key()
        test_bisect_left_with_key()
        print("All tests passed!")
    except AssertionError as e:
        print(f"Test failed: {e}")
        sys.exit(1)
