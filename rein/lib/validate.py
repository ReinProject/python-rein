#!/usr/bin/env python
import bitcoinsig
import bitcoinecdsa
import re
import os
import json
import config
import click
from document import Document, Base

def strip_armor(sig, dash_space=False):
    '''Removes ASCII-armor from a signed message by default exlcudes 'dash-space' headers'''
    sig = sig.replace('- ----', '-'*5) if dash_space else sig
    sig = re.sub("-{5}BEGIN BITCOIN SIGNED MESSAGE-{5}", "", sig)
    sig = re.sub(
        "\n+-{5}BEGIN SIGNATURE-{5}[\n\dA-z+=/]+-{5}END BITCOIN SIGNED MESSAGE-{5}\n*",
        "",
        sig
    )
    sig = re.sub("^\n", "", sig)
    sig = re.sub("\n\n", "", sig)
    return sig

def parse_sig(sig):
    '''
    Takes an ASCII-armored signature and returns a dictionary of its info.
    Returns the signature string, the signing key, and all of the information
    assigned within the message, for example:
       parse_sig(sig)['Name/handle'] === "David Sterry"
    '''
    matches = re.finditer("(.+):\s(.+)\n", sig)
    ret = {}
    for match in matches:
        ret[match.group(1)] = match.group(2)
    m = re.search(
        "-{5}BEGIN SIGNATURE-{5}\n([A-z\d=+/]+)\n([A-z\d=+/]+)"
        "\n-{5}END BITCOIN SIGNED MESSAGE-{5}",
        sig
    )
    if m:
        ret['signature_address'] = m.group(1)
        ret['signature'] = m.group(2)
    else:
        return False
    return ret

def verify_sig(sig):
    '''The base function for verifying an ASCII-armored signature.'''
    sig_info = parse_sig(sig)
    if sig_info != False:
        #valid = bitcoinsig.verify_message(
        message = strip_armor(sig)
        valid = bitcoinecdsa.verify(
            sig_info['signature_address'],
            message,
            sig_info['signature']
        )
    else:
        valid = False
    return {'valid': valid, 'info': sig_info}

def validate_enrollment(enrollment_signature_text):
    a = verify_sig(enrollment_signature_text)
    if a['valid'] != False:
        return a 
    else:
        return False

def enroll(session, engine, user):
    Base.metadata.create_all(engine)
    enrollment = "Rein User Enrollment\nUser: %s\nContact: %s\nMaster signing address: %s\nDelegate signing address: %s\n" % (user.name, user.contact, user.maddr, user.daddr)
    f = open(config.enroll_filename, 'w')
    f.write(enrollment)
    f.close()
    click.echo("\n%s\n" % enrollment)
    done = False
    while not done:
        filename = click.prompt("File containing signed statement", type=str, default=config.sig_enroll_filename)
        if os.path.isfile(filename):
            done = True
    f = open(filename, 'r')
    signed = f.read()
    res = validate_enrollment(signed)
    if res:
        # insert signed document into documents table as type 'enrollment'
        document = Document('enrollment', signed, sig_verified=True)
        session.add(document)
        session.commit()
    return res
   
def validate_review(reviewer_text):
    a = verify_sig(reviewer_text)
    return [
        a['valid'],
        a['info']['signing_address'],
        strip_armor(reviewer_text).replace('- ----', '-----')
    ]

def validate_audit(auditor_text):
    a = verify_sig(auditor_text)
    txt = strip_armor(auditor_text)
    ret = ""
    b = "- ----BEGIN BITCOIN SIGNED MESSAGE-----"
    c = "- ----BEGIN SIGNATURE-----"
    d = "- ----END BITCOIN SIGNED MESSAGE-----"
    for line in txt.splitlines():
        if line == b and ret.count(b[2:]) == 0:
            line = line.replace('- ----', '-----')
        elif line == c and ret.count(c[2:]) == 1:
            line = line.replace('- ----', '-----')
        elif line == d and ret.count(d[2:]) == 1:
            line = line.replace('- ----', '-----')
        ret += line + '\n'
    return [
        a[0],
        a[1]['signing_address'],
        ret
    ]

if __name__ == "__main__":
    # enrollment sig
    sig = """-----BEGIN BITCOIN SIGNED MESSAGE-----
Name/handle: Test Person
Contact: tester@example.com
Master signing address: 1CptxARjqcfkVwGFSjR82zmPT8YtRMubub
Delegate signing address: 1Djp4Siv5iLJUgXq5peWCDcHVWV1Mv3opc
-----BEGIN SIGNATURE-----
1CptxARjqcfkVwGFSjR82zmPT8YtRMubub
H59sadjpiAgK6LaoiLEuZ3sSoFo6S2dSIjmETszVRGI6lccEgCaEgy7na1waF8TxHiVrV6qjha3m2Ih6ynAvGps=
-----END BITCOIN SIGNED MESSAGE-----"""
    # review sig
    sig2 = """-----BEGIN BITCOIN SIGNED MESSAGE-----
- ----BEGIN BITCOIN SIGNED MESSAGE-----
Name/Handle: Knightdk
Contact: knightdk on Bitcointalk.org
Master signing address: 16mT7jrpkjnJBD7a3TM2awyxHub58H6r6Z
Delegate signing address: N/A
Willing to mediate: Y
Mediation public key: 04594f2582c859c4f65084ee7fe8e9ec2d695bb988a3f53db48eaaff6ff3a0282b2be0c79fefca01277404d0fdc3a923e8ed02efd6ab96980f3e229a81fbe032e9
- ----BEGIN SIGNATURE-----
16mT7jrpkjnJBD7a3TM2awyxHub58H6r6Z
GxHE6iJH2aMpsRk7cszvXsLieDawzArpt7XDdOPhVFD5KVqIvKve1fwUKeN6ct4bld41XLdrZ7Dvaj7x1Oiw0uo=
- ----END BITCOIN SIGNED MESSAGE-----
-----BEGIN SIGNATURE-----
1BbgnPQYeXAt39ifLNUWP1RBktpzGLmRZS
IGJcg+MoqpBQNtptelyZfC2zBKk5SZQQjtf4pHSxb0yZH6kn/9Dhd1TWFfXUXsWmZq78xYye4lKi1aQUeNQ2ZFs=
-----END BITCOIN SIGNED MESSAGE-----"""
    # audit sig
    sig3 = """-----BEGIN BITCOIN SIGNED MESSAGE-----
- ----BEGIN BITCOIN SIGNED MESSAGE-----
- ----BEGIN BITCOIN SIGNED MESSAGE-----
Name/Handle: Knightdk
Contact: knightdk on Bitcointalk.org
Master signing address: 16mT7jrpkjnJBD7a3TM2awyxHub58H6r6Z
Delegate signing address: N/A
Willing to mediate: Y
Mediation public key: 04594f2582c859c4f65084ee7fe8e9ec2d695bb988a3f53db48eaaff6ff3a0282b2be0c79fefca01277404d0fdc3a923e8ed02efd6ab96980f3e229a81fbe032e9
- ----BEGIN SIGNATURE-----
16mT7jrpkjnJBD7a3TM2awyxHub58H6r6Z
GxHE6iJH2aMpsRk7cszvXsLieDawzArpt7XDdOPhVFD5KVqIvKve1fwUKeN6ct4bld41XLdrZ7Dvaj7x1Oiw0uo=
- ----END BITCOIN SIGNED MESSAGE-----
- ----BEGIN SIGNATURE-----
1BbgnPQYeXAt39ifLNUWP1RBktpzGLmRZS
IGJcg+MoqpBQNtptelyZfC2zBKk5SZQQjtf4pHSxb0yZH6kn/9Dhd1TWFfXUXsWmZq78xYye4lKi1aQUeNQ2ZFs=
- ----END BITCOIN SIGNED MESSAGE-----
-----BEGIN SIGNATURE-----
1DVK9Rdi2wcpcfEkep7FSNUui7fzadmxsW
IMcU7MvLl7T+hY0mmMw6mblLstnXd9Ly36z7uYMqv7ZZEuZQOvuXN2GjYU0Nq4So9GKQRkQwIis7EiN6luTMcOY=
-----END BITCOIN SIGNED MESSAGE-----"""

    # Test all of the functions
    print(validate_enrollment(sig))
    print(validate_review(sig2))
    print(validate_audit(sig3))

    # Passing the output through all of the functions
    print(validate_enrollment(validate_review(validate_audit(sig3)[2])[2])[0])
    print(validate_enrollment(validate_review(sig2)[2])[0])
    print(validate_enrollment(sig1)[0])
