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

def get_user_name(log, url, user, rein, msin):
    """Find a user's name by his msin"""

    from .io import safe_get

    sel_url = "{0}query?owner={1}&delegate={2}&query=get_user_name&testnet={3}&msin={4}"
    data = safe_get(log, sel_url.format(url, user.maddr, user.daddr, rein.testnet, msin))
    data = data['get_user_name']

    # If there was a server-side error, return None
    if 'error' in data or not data:
        return 'No username found'

    user = document_to_dict(data[0]['value'])
    return user['User']

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