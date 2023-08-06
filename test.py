for _ in range(int(input())):
    n = int(input())
    a = list(map(int, input().split()))
    if n == 0:
        print(0)
        continue
    ans = 0
    for i in range(n - 1):
        if a[i + 1] < a[i]:
            ans = max(ans, a[i])
    print(ans)