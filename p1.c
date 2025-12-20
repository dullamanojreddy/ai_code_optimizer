#include <stdio.h>

int main() {
    int arr[5] = {1, 2, 3, 4, 5};
    int sum = 0;

    // Inefficient: repeatedly adding using nested loops
    for (int i = 0; i < 5; i++) {
        for (int j = 0; j <= i; j++) {
            if (j == i)
                sum += arr[i];
        }
    }

    printf("Sum: %d\n", sum);
    return 0;
}
