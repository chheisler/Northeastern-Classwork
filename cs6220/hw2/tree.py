# calculate entropy given counts for different values
def entropy(*counts):
    total = float(sum(counts))
    result = 0
    for count in counts:
        prob = count / total
        if prob != 0:
            result -= prob * log(prob, 2)
    return result

# calculate gain given parent and children as lists of counts
def gain(parent, *children):
    total = float(sum(parent))
    result = entropy(*parent)
    seen = 0
    for child in children:
        count = sum(child)
        result -= (count / total) * entropy(*child)
        seen += count
    if seen != total:
        raise ValueError('parent and child data counts do not match')
    return result

