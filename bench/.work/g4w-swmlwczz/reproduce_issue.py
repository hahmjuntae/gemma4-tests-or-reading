import sys
sys.path.insert(0, '/work')
import bisect

try:
    print("Testing bisect_right with lo=0")
    bisect.bisect_right([1, 2, 3], 2, lo=0)
    print("bisect_right(lo=0) passed")
except ValueError as e:
    print(f"bisect_right(lo=0) failed with: {e}")

try:
    print("\nTesting bisect_left with lo=0")
    bisect.bisect_left([1, 2, 3], 2, lo=0)
    print("bisect_left(lo=0) passed")
except ValueError as e:
    print(f"bisect_left(lo=0) failed with: {e}")

try:
    print("\nTesting bisect_right with lo=-1")
    bisect.bisect_right([1, 2, 3], 2, lo=-1)
    print("bisect_right(lo=-1) passed")
except ValueError as e:
    print(f"bisect_right(lo=-1) failed with: {e}")

