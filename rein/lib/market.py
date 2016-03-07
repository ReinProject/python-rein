from document import Document, get_documents_by_job_id, get_document_type, calc_hash
from validate import validate_enrollment, parse_document
from bucket import get_urls
from bitcoinecdsa import sign, verify, pubkey, pubkey_to_address
from order import Order
import os
import click
from ui import shorten, get_choice


def mediator_prompt(rein, eligible_mediators):
    mediators = unique(eligible_mediators, 'Mediator public key')
    key = pubkey(rein.user.dkey)
    i = 0
    for m in mediators:
        if m["Mediator public key"] == key:
            mediators.remove(m)
            continue
        click.echo('%s - %s - Fee: %s - Public key: %s' % (str(i), m['User'], m['Mediator fee'], m['Mediator public key']))
        i += 1
    if len(mediators) == 0:
        click.echo("None found.")
        return None
    choice = get_choice(mediators, 'mediator')
    if choice == 'q':
        return False
    return mediators[choice]

# called in offer()
def bid_prompt(rein, bids):
    """
    Prompts user to choose a bid on one of their jobs. This means they should be the job creator and
    not the worker or mediator.
    """
    i = 0
    valid_bids = []
    key = pubkey(rein.user.dkey)
    for b in bids:
        if 'Description' not in b or b['Job creator public key'] != key:
            continue 
        click.echo('%s - %s - %s - %s - %s BitCoin' % (str(i), b['Job name'], b["Worker"],
                                                  shorten(b['Description']), b['Bid amount (BTC)']))
        valid_bids.append(b)
        i += 1
    if len(valid_bids) == 0:
        click.echo('No bids available.')
        return None
    choice = get_choice(valid_bids, 'bid')
    if choice == 'q':
        click.echo('None chosen.')
        return False
    bid = valid_bids[choice]
    click.echo('You have chosen %s\'s bid.\n\nFull description: %s\nBid amount (BTC): %s\n\nPlease review carefully before accepting. (Ctrl-c to abort)' % 
               (bid['Worker'], bid['Description'], bid['Bid amount (BTC)']))
    return bid


def job_prompt(rein, jobs):
    """
    Prompt user for jobs they can bid on. Filters out jobs they created or are mediator for.
    """
    key = pubkey(rein.user.dkey)
    valid_jobs = []
    for j in jobs:
        if j['Job creator public key'] != key and j['Mediator public key'] != key:
            valid_jobs.append(j)
        
    i = 0
    for j in valid_jobs:
        click.echo('%s - %s - %s - %s' % (str(i), j["Job creator"],
                                          j['Job name'], shorten(j['Description'])))
        i += 1
    choice = get_choice(jobs, 'job')
    if choice == 'q':
        return False
    job = jobs[choice]
    click.echo('You have chosen a Job posted by %s.\n\nFull description: %s\n\nPlease pay attention '
               'to each requirement and provide a time frame to complete the job. (Ctrl-c to abort)\n' % 
               (job['Job creator'], job['Description']))
    return job


def delivery_prompt(rein, choices, detail='Description'):
    choices = unique(choices, 'Job ID')
    i = 0
    for c in choices:
        if 'Bid amount (BTC)' not in c:
            continue
        if detail in c:
            click.echo('%s - %s - %s BTC - %s' % (str(i), c['Job name'], c['Bid amount (BTC)'], shorten(c[detail])))
        else:
            click.echo('%s - %s - %s BTC - %s' % (str(i), c['Job name'], c['Bid amount (BTC)'], shorten(c['Description'])))
        i += 1
    choice = get_choice(choices, 'job')
    if choice == 'q':
        return None
    chosen = choices[choice]
    click.echo('You have chosen to post deliverables. The following is from your winning bid.'
               '\n\nDescription: %s\n\nPlease review carefully before posting deliverables. '
               'This will be public and reviewed by mediators if disputed. (Ctrl-c to abort)\n' % 
               (chosen['Description'],))
    return chosen


def accept_prompt(rein, choices, detail='Description'):
    i = 0
    for c in choices:
        if 'Primary escrow redeem script' not in c:
            continue
        if detail in c:
            click.echo('%s - %s - %s - %s' % (str(i), c['Job name'], c['Job ID'], shorten(c[detail])))
        else:
            click.echo('%s - %s - %s - %s' % (str(i), c['Job name'], c['Job ID'], shorten(c['Description'])))
        i += 1
    choice = get_choice(choices, 'delivery')
    if choice == 'q':
        return None
    chosen = choices[choice]
    if detail in chosen:
        contents = chosen[detail]
    else:
        contents = chosen['Description']
    click.echo('You have chosen to accept the following deliverables. \n\n%s: %s\nAccepted Bid amount (BTC): %s\n'
               'Primary escrow redeem script: %s\n'
               'Worker address: %s\n\n'
               'Mediator escrow redeem script: %s\n'
               'Mediator address: %s\n'
               '\nPlease review carefully before accepting. Once you upload your signed statement, the mediator should no '
               'longer provide a refund. (Ctrl-c to abort)\n' % 
               (detail,
                contents, chosen['Bid amount (BTC)'],
                chosen['Primary escrow redeem script'],
                pubkey_to_address(chosen['Worker public key']),
                chosen['Mediator escrow redeem script'],
                pubkey_to_address(chosen['Mediator public key'])
               )
              )
    return chosen


def dispute_prompt(rein, choices, detail='Description'):
    i = 0
    for c in choices:
        if 'Primary escrow redeem script' not in c:
            continue
        if detail in c:
            click.echo('%s - %s - %s - %s' % (str(i), c['Job name'], c['Job ID'], shorten(c[detail])))
        else:
            click.echo('%s - %s - %s - %s' % (str(i), c['Job name'], c['Job ID'], shorten(c['Description'])))
        i += 1
    choice = get_choice(choices, 'job')
    if choice == 'q':
        return None
    chosen = choices[choice]
    if detail in chosen:
        contents = chosen[detail]
    else:
        contents = chosen['Description']
    click.echo('You have chosen to dispute the following deliverables. \n\n%s: %s\n\nPlease provide as much detail as possible. '
               'For the primary payment, you should build and sign one that refunds you at %s. (Ctrl-c to abort)\n' % 
               (detail, contents, rein.user.daddr))
    return chosen


def resolve_prompt(rein, choices, detail='Dispute detail'):
    i = 0
    for c in choices:
        if 'Primary escrow redeem script' not in c:
            continue
        click.echo('%s - %s - %s - %s' % (str(i), c['Job name'], c['Job ID'], shorten(c[detail])))
        i += 1
    choice = get_choice(choices, 'dispute')
    if choice == 'q':
        return None
    chosen = choices[choice]
    click.echo('You have chosen to resolve this dispute. \n\n%s: %s\n\n'
               'For the mediator payment, you should build and sign one that pays you at %s. (Ctrl-c to abort)\n' %
               (detail, chosen[detail], rein.user.daddr))
    return chosen


def assemble_document(title, fields):
    """
    Prompts to fill in any gaps in form values, then builds document with all fields.
    """
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
        elif 'not_null' in field.keys() and field['not_null']:
            entry['value'] = field['not_null'][field['label']]
        else:
            entry['value'] = click.prompt(field['label'])
        data.append(entry)
    document = "Rein %s\n" % title
    for entry in data:
        document = document + entry['label'] + ": " + entry['value'] + "\n"
    return document[:-1]


def sign_and_store_document(rein, doc_type, document, signature_address=None, signature_key=None, store=True):
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
        if store:
            d = Document(rein, doc_type, signed, sig_verified=True, testnet=rein.testnet)
            rein.session.add(d)
            rein.session.commit()
        return d
    return validated

def assemble_order(rein, document):
    """
    Take one document and build the entire order based on it. The idea here is that one Job ID should
    allow us to query each available server for each document type that is associated with it, then
    filter out bogus shit by focusing on who's signed correct stuff. This kind of command can also
    look for attempted changes in foundational info like participants public keys and redeem scripts.
    If this works well, we can reduce how much data is required at each stage. Finally, we should
    be able to serialize a job from end to end so it can be easily reviewed by a mediator.
    """
    parsed = parse_document(document.contents)
    if 'Job ID' not in parsed:
        return 0
    job_id = parsed['Job ID']
    urls = get_urls(rein)
    documents = []
    if job_id:
        for url in urls:
            res = get_documents_by_job_id(rein, url, job_id)
            if res:
                documents += res
        order_id = Order.get_order_id(rein, job_id)
        if not order_id:
            o = Order(job_id, testnet=rein.testnet)
            rein.session.add(o)        
            rein.session.commit()

    for document in documents:
        doc_type = get_document_type(document)
        if not doc_type:
            rein.log.info('doc_type not detected')
            continue
        doc_hash = calc_hash(document)
        d = rein.session.query(Document).filter(Document.doc_hash == doc_hash).first()
        if d:
            d.set_order_id(order_id)
        else:
            new_document = Document(rein, doc_type, document, order_id, 'external', source_key=None, sig_verified=True, testnet=rein.testnet)
            rein.session.add(new_document)

        rein.session.commit()

    return len(documents)
    # how do we test this? give it a document, it gets the job id, then does a query for all other docs 
    # with that job id. if it can figure out the doc type, it sets the order id on it. this allows
    # Order.get_documents() to provide all documents or to provide just the post or the bid.

def unique(the_array, key):
    """
    Filter an array of dicts by key
    """
    unique = []
    values = []
    for element in the_array:
        if key in element and element[key] not in values:
            values.append(element[key])
            unique.append(element)
    return unique
