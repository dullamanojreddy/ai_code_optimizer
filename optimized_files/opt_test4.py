def find_duplicates(items):
    seen = set()
    dupes = set()
    for item in items:
        if item in seen:
            dupes.add(item)
        else:
            seen.add(item)
    return list(dupes)