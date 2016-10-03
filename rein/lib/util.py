
def unique(the_array, key=None):
    """
    Filter an array of dicts by key. Only lets through dicts that include key.
    """
    unique = []
    values = []
    for element in the_array:
        if key:
            if key in element and element[key] not in values:
                values.append(element[key])
                unique.append(element)
        else:
            if element not in unique:
                unique.append(element)
    return unique
