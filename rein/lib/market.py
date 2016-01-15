from document import Document
from validate import validate_enrollment
from bitcoinecdsa import sign, verify
import os
import click


def mediator_prompt(rein, eligible_mediators):
    i = 0
    for m in eligible_mediators:
        click.echo('%s - %s %s' % (str(i), m['User'], m['Mediation fee']))
        i += 1
    choice = -1
    while choice >= len(eligible_mediators) or choice < 0:
        choice = click.prompt('Choose a mediator', type=int)
    return eligible_mediators[choice]


def bid_prompt(rein, bids):
    i = 0
    valid_bids = []
    for b in bids:
        if 'Description' not in b:
            continue 
        trimmed_description = b['Description'][0:59]
        if len(trimmed_description) == 60:
            trimmed_description += '...'
        click.echo('%s - %s - %s - %s BitCoin' % (str(i), b["Worker's name"], trimmed_description, b['Bid amount (BTC)']))
        valid_bids.append(b)
        i += 1
    if len(valid_bids) == 0:
        return None
    choice = -1
    while(choice >= len(bids) or choice < 0) and choice != 'q':
        choice = click.prompt('Choose a bid (q to quit)', type=str)
        try:
            choice = int(choice)
        except:
            choice = choice
    if choice == 'q':
        return False
    bid = valid_bids[choice]
    click.echo('You have chosen %s\'s bid.\n\nFull description: %s\n\nPlease review carefully before accepting.' % 
               (bid['Worker\'s name'], bid['Description']))
    return bid


def job_prompt(rein, jobs):
    i = 0
    for j in jobs:
        trimmed_description = j['Description'][0:59]
        if len(trimmed_description) == 60:
            trimmed_description += '...'
        click.echo('%s - %s - %s - %s' % (str(i), j["Job creator's name"], j['Job name'], trimmed_description))
        i += 1
    choice = -1
    while(choice >= len(jobs) or choice < 0) and choice != 'q':
        choice = click.prompt('Choose a job (q to quit)', type=str)
        try:
            choice = int(choice)
        except:
            choice = choice
    if choice == 'q':
        return False
    job = jobs[choice]
    click.echo('You have chosen a Job posted by %s.\n\nFull description: %s\n\nPlease pay attention '
               'to each requirement and provide a time frame to complete the job.\n' % 
               (job['Job creator\'s name'], job['Description']))
    return job


def delivery_prompt(rein, choices, detail='Description'):
    i = 0
    for c in choices:
        if 'Bid amount (BTC)' not in c:
            continue
        trimmed_detail = c[detail][0:59]
        if len(trimmed_detail) == 60:
            trimmed_detail += '...'
        click.echo('%s - %s - %s - %s' % (str(i), c['Job ID'], c['Bid amount (BTC)'], trimmed_detail))
        i += 1
    choice = -1
    while(choice >= len(choices) or choice < 0) and choice != 'q':
        choice = click.prompt('Choose a job (q to quit)', type=str)
        try:
            choice = int(choice)
        except:
            choice = choice
    if choice == 'q':
        return None
    chosen = choices[choice]
    click.echo(chosen)
    click.echo('You have chosen to post deliverables for the following job. \n\nDescription: %s\n\nPlease review carefully before posting. '
               'In a dispute mediators are advised to consider it above other evidence.\n' % 
               (chosen['Description'],))
    return chosen


def build_document(title, fields, labels, defaults, guid=None):
    """
    Prompt for info and build a document with it.
    """
    data = []
    display_labels = {}
    for i in range(len(fields)):
        entry = {}
        entry['label'] = labels[i]
        if i + 1 > len(defaults) or defaults[i] == '':
            entry['value'] = click.prompt(labels[i])
        else:
            entry['value'] = defaults[i]
        data.append(entry)
    document = "Rein %s\n" % title
    for entry in data:
        document = document + entry['label'] + ": " + entry['value'] + "\n"
    if guid:
        document = document + "Job ID: " + guid + "\n"
    document = document[:-1]
    return document


def sign_and_store_document(rein, doc_type, document, signature_address=None, signature_key=None):
    """
    Save document if no signature key provided. Otherwise sign document, then validate and store it.
    """
    validated = False
    if signature_key is None:  # signing will happen outside app
        f = open(doc_type + '.txt', 'w')
        f.write(document)
        f.close()
        click.echo("\n%s\n" % document)
        done = False
        while not done:
            filename = click.prompt("File containing signed document", type=str, default=doc_type + '.sig.txt')
            if os.path.isfile(filename):
                done = True
        f = open(filename, 'r')
        signed = f.read()
        res = validate_enrollment(signed)
        if res:
            validated = True
    else:                       # sign with stored delegate key
        signature = sign(signature_key, document)
        validated = verify(signature_address, document, signature)

    if validated:
        # insert signed document into documents table
        b = "-----BEGIN BITCOIN SIGNED MESSAGE-----"
        c = "-----BEGIN SIGNATURE-----"
        d = "-----END BITCOIN SIGNED MESSAGE-----"
        signed = "%s\n%s\n%s\n%s\n%s\n%s" % (b, document, c, signature_address, signature, d)
        click.echo('\n' + signed + '\n')
        d = Document(rein, doc_type, signed, sig_verified=True)
        rein.session.add(d)
        rein.session.commit()
    return validated


def create_signed_document(rein, title, doc_type, fields, labels, defaults,
                           signature_address=None, signature_key=None, guid=None):
    """
    Save or sign document, then validate and store it.
    """
    data = []
    display_labels = {}
    # instead of two dicts we should just use one dict
    # entry = { 'label': 'whatever',
    #         'value': 42 }

    for i in range(len(fields)):
        entry = {}
        entry['label'] = labels[i]
        if i + 1 > len(defaults) or defaults[i] == '':
            entry['value'] = click.prompt(labels[i])
        else:
            entry['value'] = defaults[i]
        data.append(entry)

    # passed as defaults, put defaults first to avoid having to pass lots of '' defaults
    # user = session.query(User).first()
    # key = pubkey(user.dkey)

    display = "Rein %s\n" % title
    for entry in data:
        display = display + entry['label'] + ": " + entry['value'] + "\n"
    if guid:
        display = display + "Job ID: " + guid + "\n"
    display = display[:-1]

    validated = False
    if signature_key is None:  # signing will happen outside app
        f = open(doc_type + '.txt', 'w')
        f.write(display)
        f.close()
        click.echo("\n%s\n" % display)
        done = False
        while not done:
            filename = click.prompt("File containing signed job posting", type=str, default=doc_type + '.sig.txt')
            if os.path.isfile(filename):
                done = True
        f = open(filename, 'r')
        signed = f.read()
        res = validate_enrollment(signed)
        if res:
            validated = True
    else:                       # sign with stored delegate key
        signature = sign(signature_key, display)
        validated = verify(signature_address, display, signature)

    if validated:
        # insert signed document into documents table
        b = "-----BEGIN BITCOIN SIGNED MESSAGE-----"
        c = "-----BEGIN SIGNATURE-----"
        d = "-----END BITCOIN SIGNED MESSAGE-----"
        signed = "%s\n%s\n%s\n%s\n%s\n%s" % (b, display, c, signature_address, signature, d)
        click.echo('\n' + signed + '\n')
        document = Document(rein, doc_type, signed, sig_verified=True)
        rein.session.add(document)
        rein.session.commit()
    return validated
