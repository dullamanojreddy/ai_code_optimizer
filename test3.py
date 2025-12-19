# test3.py
total_sum = 0
def calculate_total(data):
    global total_sum
    for x in data:
        total_sum += x
    return total_sum