#include <iostream>
using namespace std;

// Inefficient: naive recursive Fibonacci (exponential time)
int fib(int n) {
    if (n <= 1)
        return n;
    return fib(n-1) + fib(n-2);
}

int main() {
    int n = 10;
    cout << "Fibonacci of " << n << " is " << fib(n) << endl;
    return 0;
}
