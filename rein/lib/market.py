from document import Document
from validate import validate_enrollment
from bitcoinecdsa import sign, verify
import os
import click


def mediator_prompt(rein, eligible_mediators):
    i = 0
    for m in eligible_mediators:
        click.echo('%s - %s %s' % (str(i + 1), m['User'], m['Mediation fee']))
        i += 1
    choice = 0
    while choice > len(eligible_mediators) or choice < 1:
        choice = click.prompt('Please choose a mediator', type=int)
    index = choice - 1
    return eligible_mediators[index]


def create_signed_document(rein, title, doc_type, fields, labels, defaults,
                           signature_address=False, signature_key=False):
    """
    Prompt for info, save to file, validate and store signed document.
    """
    click.echo("Post " + title)

    data = {}
    display_labels = {}

    for i in range(len(fields)):
        display_labels[fields[i]] = labels[i]
        if i + 1 > len(defaults) or defaults[i] == '':
            data[fields[i]] = click.prompt(labels[i])
        else:
            data[fields[i]] = defaults[i]

    # passed as defaults, put defaults first to avoid having to pass lots of '' defaults
    # user = session.query(User).first()
    # key = pubkey(user.dkey)

    display = "Rein %s\n" % title
    for key in data.keys():
        display = display + display_labels[key] + ": " + data[key] + "\n"

    validated = False
    if signature_key is False:  # signing will happen outside app
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
        # insert signed document into documents table as type 'enrollment'
        b = "-----BEGIN BITCOIN SIGNED MESSAGE-----"
        c = "-----BEGIN SIGNATURE-----"
        d = "-----END BITCOIN SIGNED MESSAGE-----"
        signed = "%s\n%s\n%s\n%s\n%s\n%s\n" % (b, display, c, signature_address, signature, d)
        document = Document(rein, doc_type, signed, sig_verified=True)
        rein.session.add(document)
        rein.session.commit()
    return validated
