import math

def factorial(n: int) -> int:
    """
    Calculates the factorial of n using the highly optimized C implementation
    in Python's standard library.
    """
    if n < 0:
        raise ValueError("factorial() not defined for negative values")
    return math.factorial(n)

if __name__ == "__main__":
    print(factorial(5))