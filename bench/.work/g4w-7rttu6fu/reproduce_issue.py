import bisect

arr = [1, 2, 2, 2, 3]
keyfunc = lambda x: x
x = 2

# bisect_right should return 4
result = bisect.bisect_right(arr, x, key=keyfunc)
print(f"bisect_right(arr, {x}, key=keyfunc) = {result}, expected 4")

arr = [1, 2, 2, 2, 3]
keyfunc = lambda x: x
x = 2

# bisect_left should return 1
result = bisect.bisect_left(arr, x, key=keyfunc)
print(f"bisect_left(arr, {x}, key=keyfunc) = {result}, expected 1")

