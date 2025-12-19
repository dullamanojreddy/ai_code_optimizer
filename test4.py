# test4.py
def find_duplicates(items):
    dupes = []
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            if items[i] == items[j] and items[i] not in dupes:
                dupes.append(items[i])
    return dupes