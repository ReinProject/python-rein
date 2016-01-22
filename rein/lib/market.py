from document import Document
from validate import validate_enrollment
from bitcoinecdsa import sign, verify
import os
import click
from ui import shorten, get_choice


def mediator_prompt(rein, eligible_mediators):
    unique = []
    pubkeys = []
    for m in eligible_mediators:
        if m['Mediator public key'] not in pubkeys:
            pubkeys.append(m['Mediator public key'])
            unique.append(m)
    i = 0
    for m in unique:
        click.echo('%s - %s - Fee: %s - Public key: %s' % (str(i), m['User'], m['Mediator fee'], m['Mediator public key']))
        i += 1
    if len(unique) == 0:
        return None
    choice = get_choice(unique, 'mediator')
    if choice == 'q':
        return False
    return unique[choice]


def bid_prompt(rein, bids):
    i = 0
    valid_bids = []
    for b in bids:
        if 'Description' not in b:
            continue 
        click.echo('%s - %s - %s - %s BitCoin' % (str(i), b["Worker's name"],
                                                  shorten(b['Description']), b['Bid amount (BTC)']))
        valid_bids.append(b)
        i += 1
    if len(valid_bids) == 0:
        return None
    choice = get_choice(valid_bids, 'bid')
    if choice == 'q':
        return False
    bid = valid_bids[choice]
    click.echo('You have chosen %s\'s bid.\n\nFull description: %s\n\nPlease review carefully before accepting. (Ctrl-c to abort)' % 
               (bid['Worker\'s name'], bid['Description']))
    return bid


def job_prompt(rein, jobs):
    i = 0
    for j in jobs:
        click.echo('%s - %s - %s - %s' % (str(i), j["Job creator's name"],
                                          j['Job name'], shorten(j['Description'])))
        i += 1
    choice = get_choice(jobs, 'job')
    if choice == 'q':
        return False
    job = jobs[choice]
    click.echo('You have chosen a Job posted by %s.\n\nFull description: %s\n\nPlease pay attention '
               'to each requirement and provide a time frame to complete the job. (Ctrl-c to abort)\n' % 
               (job['Job creator\'s name'], job['Description']))
    return job


def delivery_prompt(rein, choices, detail='Description'):
    i = 0
    for c in choices:
        if 'Bid amount (BTC)' not in c:
            continue
        click.echo('%s - %s - %s - %s' % (str(i), c['Job ID'], c['Bid amount (BTC)'], shorten(c[detail])))
        i += 1
    choice = get_choice(choices, 'job')
    if choice == 'q':
        return None
    chosen = choices[choice]
    click.echo('You have chosen to post deliverables for the following job. \n\nDescription: %s\n\nPlease review carefully before posting. '
               'In a dispute mediators are advised to consider it above other evidence. (Ctrl-c to abort)\n' % 
               (chosen['Description'],))
    return chosen


def accept_prompt(rein, choices, detail='Description'):
    i = 0
    for c in choices:
        if 'Primary escrow redeem script' not in c:
            continue
        click.echo('%s - %s - %s' % (str(i), c['Job ID'], shorten(c[detail])))
        i += 1
    choice = get_choice(choices, 'delivery')
    if choice == 'q':
        return None
    chosen = choices[choice]
    click.echo('You have chosen to accept the following deliverables. \n\n%s: %s\n\nPlease review carefully before accepting. '
               'Once you upload your signed statement, the mediator should no longer provide a refund. (Ctrl-c to abort)\n' % 
               (detail, chosen[detail]))
    return chosen


def creatordispute_prompt(rein, choices, detail='Description'):
    i = 0
    for c in choices:
        if 'Primary escrow redeem script' not in c:
            continue
        click.echo('%s - %s - %s' % (str(i), c['Job ID'], shorten(c[detail])))
        i += 1
    choice = get_choice(choices, 'delivery')
    if choice == 'q':
        return None
    chosen = choices[choice]
    click.echo('You have chosen to dispute the following deliverables. \n\n%s: %s\n\nPlease provide as much detail as possible. '
               'For the primary payment, you should build and sign one that refunds you at %s. (Ctrl-c to abort)\n' % 
               (detail, chosen[detail], rein.user.daddr))
    return chosen


def workerdispute_prompt(rein, choices, detail='Description'):
    i = 0
    for c in choices:
        if 'Primary escrow redeem script' not in c:
            continue
        click.echo('%s - %s - %s' % (str(i), c['Job ID'], shorten(c[detail])))
        i += 1
    choice = get_choice(choices, 'delivery')
    if choice == 'q':
        return None
    chosen = choices[choice]
    click.echo('You have chosen to dispute the following deliverables. \n\n%s: %s\n\nPlease provide as much detail as possible. '
               'For the primary payment, you should build and sign one that pays you at %s. (Ctrl-c to abort)\n' % 
               (detail, chosen[detail], rein.user.daddr))
    return chosen


def assemble_document(title, fields):
    data = []
    for field in fields:
        entry = {}
        entry['label'] = field['label']
        if 'validator' in field.keys():
            valid = False
            while not valid:
                answer = click.prompt(field['label'])
                valid = field['validator'](answer)
            entry['value'] = answer
        elif 'value' in field.keys():
            entry['value'] = field['value']
        elif 'value_from' in field.keys():
            entry['value'] = field['value_from'][field['label']]
        else:
            entry['value'] = click.prompt(field['label'])
        data.append(entry)
    document = "Rein %s\n" % title
    for entry in data:
        click.echo(entry['label'])
        click.echo(entry['value'])
        document = document + entry['label'] + ": " + entry['value'] + "\n"
    return document[:-1]


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

def join_documents(rein, document):
    """
    Take one document and build the entire order based on it. The idea here is that one Job ID should
    allow us to query each available server for each document type that is associated with it, then
    filter out bogus shit by focusing on who's signed correct stuff. This kind of command can also
    look for attempted changes in foundational info like participants public keys and redeem scripts.
    Finally, if this works well, we can reduce how much data is required at each stage. Finally still,
    we should be able to serialize a job from end to end so it can be easily reviewed by a mediator.
    """
    job_id = get_job_id(document)
    urls = get_urls(rein)
    documents = []
    if job_id:
        for url in urls:
            documents += get_documents_by_job_id(rein, url, job_id)

    for contents in documents:
        doc_type = get_doc_type(contents)
        if not doc_type:
            rein.log.info('doc_type not detected')
            continue
        d = Document(rein, doc_type, contents, url)
        order_id = Order.get_order_id(job_id)
        if order_id:
            d.set_order_id(order_id)
        else:
            o = Order(job_id)
            rein.db.add(o)        
    rein.db.commit()
    # how do we test this? give it a document, it gets the job id, then does a query for all other docs 
    # with that job id. if it can figure out the doc type, it sets the order id on it. this allows
    # Order.get_documents() to provide all documents or to provide just the post or the bid.
