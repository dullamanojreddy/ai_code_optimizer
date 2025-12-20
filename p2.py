def factorial(n):
    result = 1
    # Inefficient: multiplying n times for each number recursively
    for i in range(1, n+1):
        for j in range(1, i+1):
            if j == i:
                result *= i
    return result

print(factorial(5))
