import sys
import os

# Ensure we import the bisect from /work
sys.path.insert(0, '/work')
import bisect

try:
    # This should work but will fail if the bug is present
    bisect.bisect_right([1, 2, 3], 2, lo=0)
    print("Success: bisect_right with lo=0 worked")
except ValueError as e:
    print(f"Failure: bisect_right with lo=0 raised {e}")
except Exception as e:
    print(f"Unexpected exception: {e}")

try:
    # This should also work
    bisect.bisect_left([1, 2, 3], 2, lo=0)
    print("Success: bisect_left with lo=0 worked")
except ValueError as e:
    print(f"Failure: bisect_left with lo=0 raised {e}")
except Exception as e:
    print(f"Unexpected exception: {e}")
