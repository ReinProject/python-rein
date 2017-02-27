def document_to_dict(content):
    """Turns a document's contents into a dict"""

    doc = {}
    try:
        # Grab part of the document containing information
        content = content.split('\n-----BEGIN SIGNATURE-----')[0]
        # Remove heading
        content = content.split('\n')[2:]
        for line in content:
            key_value = line.split(': ')
            key = key_value[0]
            value = key_value[1]
            doc[key] = value

    except:
        return {'error': 'unspecified error'}

    return doc

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