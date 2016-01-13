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


def job_prompt(rein, jobs):
    i = 0
    for j in jobs:
        click.echo('%s - %s - %s' % (str(i), j["Job creator's name"], j['Description'][0:60]))
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
    click.echo('You have chosen a Job posted by %s.\nFull description:\n\n%s\n\nPlease pay attention '
               'to each requirement as you create your bid and provide a time frame to '
               'complete the job.\n' % (job['Job creator\'s name'], job['Description']))
    return job


def create_signed_document(rein, title, doc_type, fields, labels, defaults,
                           signature_address=None, signature_key=None, guid=None):
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
