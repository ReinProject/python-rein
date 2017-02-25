def yes_or_no(question):
    reply = str(input(question + ' (y/n): ')).lower().strip()

    if len(reply) > 0 and reply[0] == 'y':
        return True
    if len(reply) > 0 and reply[0] == 'n':
        return False
    else:
        return yes_or_no(_("Please enter "))
