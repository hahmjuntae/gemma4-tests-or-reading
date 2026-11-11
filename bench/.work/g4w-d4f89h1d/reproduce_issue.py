import bisect

a = [1, 2, 3, 4, 5]
x = 3

try:
    print(f"bisect_right({a}, {x}, lo=0): {bisect.bisect_right(a, x, lo=0)}")
except Exception as e:
    print(f"bisect_right error: {e}")

try:
    print(f"bisect_left({a}, {x}, lo=0): {bisect.bisect_left(a, x, lo=0)}")
except Exception as e:
    print(f"bisect_left error: {e}")

