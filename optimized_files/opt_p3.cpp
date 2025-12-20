#include <iostream>
#include <cstdint>

/**
 * Computes the n-th Fibonacci number iteratively.
 * Time Complexity: O(n)
 * Space Complexity: O(1)
 */
constexpr uint64_t fibonacci(int n) {
    if (n <= 1) {
        return static_cast<uint64_t>(n);
    }

    uint64_t previous = 0;
    uint64_t current = 1;

    for (int i = 2; i <= n; ++i) {
        uint64_t next = previous + current;
        previous = current;
        current = next;
    }

    return current;
}

int main() {
    constexpr int n = 10;
    std::cout << "Fibonacci of " << n << " is " << fibonacci(n) << '\n';
    return 0;
}