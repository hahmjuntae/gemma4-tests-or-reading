import sys
import os

sys.path.insert(0, '/tmp')
import bisect_py_only as bisect

def test_bisect_left():
    try:
        bisect.bisect_left([1, 2, 3], 2)
        print("test_bisect_left passed")
    except ValueError as e:
        print(f"test_bisect_left failed: {e}")
    except Exception as e:
        print(f"test_bisect_left failed with unexpected exception: {type(e).__name__}: {e}")

if __name__ == "__main__":
    test_bisect_left()
