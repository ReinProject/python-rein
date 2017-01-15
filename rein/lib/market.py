from .document import Document
from .validate import validate_enrollment, parse_document, filter_and_parse_valid_sigs
from .bucket import Bucket 
from .bitcoinecdsa import sign, verify, pubkey, pubkey_to_address
from .order import Order
from .io import safe_get
from sqlalchemy import and_
import os
import click


def assemble_document(title, fields):
    """
    Prompts to fill in any gaps in form values, then builds document with all fields.
    """
    data = []
    for field in fields:
        entry = {}
        entry['label'] = field['label']
        prompt = field['label']
        if 'help' in field.keys():
            prompt = '\n' + field['help'] + '\n' + field['label']
        if 'validator' in field.keys():
            valid = False
            while not valid:
                answer = click.prompt(prompt)
                valid = field['validator'](answer)
            entry['value'] = answer
        elif 'value' in field.keys():
            entry['value'] = field['value']
        elif 'value_from' in field.keys():
            entry['value'] = field['value_from'][field['label']]
        elif 'not_null' in field.keys() and field['not_null']:
            entry['value'] = field['not_null'][field['label']]
        else:
            entry['value'] = click.prompt(prompt)
        data.append(entry)
    document = "Rein %s\n" % title
    for entry in data:
        document = document + entry['label'] + ": " + entry['value'] + "\n"
    return document[:-1]


def sign_and_store_document(rein, doc_type, document, signature_address=None, signature_key=None, store=True, overwrite_hash=None):
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
        # If document doesn't already exist, create
        if store and not overwrite_hash:
            d = Document(rein, doc_type, signed, sig_verified=True, testnet=rein.testnet)
            rein.session.add(d)
            rein.session.commit()

        # If it does exist and is supposed to be overwritten, overwrite
        elif store:
            d = rein.session.query(Document).filter(and_(Document.doc_hash == overwrite_hash, Document.doc_type == doc_type)).first()
            old_value = d.contents
            d.contents = signed
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
    urls = Bucket.get_urls(rein)
    documents = []
    if job_id:
        for url in urls:
            # queries remote server for all docs associated with a job_id
            res = Document.get_documents_by_job_id(rein, url, job_id)
            if res:
                documents += res
        order_id = Order.get_order_id(rein, job_id)
        if not order_id:
            o = Order(job_id, testnet=rein.testnet)
            rein.session.add(o)
            rein.session.commit()

    for document in documents:
        doc_type = Document.get_document_type(document)
        if not doc_type:
            rein.log.info('doc_type not detected')
            continue
        doc_hash = Document.calc_hash(document)
        d = rein.session.query(Document).filter(Document.doc_hash == doc_hash).first()
        if d:
            d.set_order_id(order_id)
            rein.session.add(d)
        else:
            new_document = Document(rein, doc_type, document, order_id, 'remote', source_key=None, sig_verified=True, testnet=rein.testnet)
            rein.session.add(new_document)
        rein.session.commit()

    return len(documents)


def get_in_process_orders(rein, Document, key, match_field, should_match):
    """
    Get a list of orders in offer or delivery states with parsed metadata 
    and validated original document

    Optionally filters documents by a matching key:value pair.

    Side effecits: updates orders
    """

    Order.update_orders(rein, Document)

    # get all documents for orders in the right states
    documents = []
    orders = Order.get_user_orders(rein, Document)
    for order in orders:
        state = order.get_state(rein, Document)
        if state in ['offer', 'delivery']:
            documents += order.get_documents(rein, Document, state)

    # attach raw contents of all order's documents
    contents = []
    for document in documents:
        contents.append(document.contents)

    valid_results = filter_and_parse_valid_sigs(rein, contents)

    # finally attach state for each document and filter by KV if necessary
    target_orders = []
    for res in valid_results:
        if (should_match and res[match_field] == key) or \
           (not should_match and res[match_field] != key):
            order = Order.get_by_job_id(rein, res['Job ID'])
            res['state'] = order.get_state(rein, Document)
            target_orders.append(res)

    return target_orders

def assemble_orders(rein, job_ids):
    """
    Take a list of job_ids and build their entire orders. The idea here is that one Job ID should
    allow us to query each available server for each document type that is associated with it, then
    filter out cruft by focusing on who's signed correctly.

    TODO: look for attempted changes in foundational info like participants public keys and redeem scripts.
    """
    urls = Bucket.get_urls(rein)
    documents = []
    arg_job_ids = ','.join(job_ids)
    for url in urls:
        # queries remote server for all docs associated with a job_id
        res = Document.get_documents_by_job_id(rein, url, arg_job_ids)
        if res:
            documents += res

    order_ids = {}
    order_id = None
    for job_id in job_ids:
        order_id = Order.get_order_id(rein, job_id)
        if not order_id:
            o = Order(job_id, testnet=rein.testnet)
            rein.session.add(o)
            rein.session.commit()
        order_id = Order.get_order_id(rein, job_id)
        order_ids[job_id] = order_id

    if not order_id:
        return 0

    for document in documents:
        doc_type = Document.get_document_type(document)
        if not doc_type:
            rein.log.info('doc_type not detected')
            continue
        doc_hash = Document.calc_hash(document)
        job_id = Document.get_job_id(document)
        d = rein.session.query(Document).filter(Document.doc_hash == doc_hash).first()
        if d:
            d.set_order_id(order_ids[job_id])
            rein.session.add(d)
        else:
            new_document = Document(rein, doc_type, document, order_id, 'remote', source_key=None, sig_verified=True, testnet=rein.testnet)
            rein.session.add(new_document)
        rein.session.commit()

    return len(documents)
