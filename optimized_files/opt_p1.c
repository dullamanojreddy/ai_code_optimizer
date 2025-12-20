#include <stdio.h>

int main(void) {
    const int arr[] = {1, 2, 3, 4, 5};
    const size_t len = sizeof(arr) / sizeof(arr[0]);
    int sum = 0;

    for (size_t i = 0; i < len; ++i) {
        sum += arr[i];
    }

    printf("Sum: %d\n", sum);
    return 0;
}