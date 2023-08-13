n, m = map(int, input().split())
a = list(map(int, input().split()))
free = set()
for elem in a:
    free.add(elem)
print(free[1])
