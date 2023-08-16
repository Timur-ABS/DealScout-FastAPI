def sieve_of_eratosthenes(n):
    sieve = [True] * (n + 1)
    sieve[0], sieve[1] = False, False
    p = 2
    while p * p <= n:
        if sieve[p]:
            for i in range(p * p, n + 1, p):
                sieve[i] = False
        p += 1
    return [i for i, v in enumerate(sieve) if v]

# Применяем алгоритм и находим все простые числа до 10^5 + 5
primes = sieve_of_eratosthenes(10**5 + 5)
print(primes)  # Если вы хотите вывести все простые числа
#
# for _ in range(int(input())):
#     n = int(input())
#     st = set()
#     print(1, end=' ')
#     st.add(1)
#     cur = 2
#     cur_s = 2
#     while cur <= n or cur_s <= n:
#         if cur_s <= n:
#             print(cur_s, end=' ')
#             st.add(cur_s)
#             cur_s *= cur
#         else:
#             while cur in st:
#                 cur += 1
#             st.add(cur)
#             cur_s = cur
#     print()
