#!/usr/bin/env python
import bitcoinsig
import re

# Removes ASCII-armor from a signed message
# by default exlcudes 'dash-space' headers
def strip_armor(sig, dash_space=False):
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

# Takes an ASCII-armored signature and returns a dictionary of it's info.
# Returns the signature string, the signing key, and all of the information
# assigned within the message, for example:
#    parse_sig(sig)['Name/handle'] === "David Sterry"
def parse_sig(sig):
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
        ret['master'] = m.group(1)
        ret['signature'] = m.group(2)
    else:
        return False
    return ret

# The base function for verifying an ASCII-armored signature.
def verify_sig(sig):
    sig_info = parse_sig(sig)
    if sig_info != False:
        valid = bitcoinsig.verify_message(
            sig_info['master'],
            sig_info['signature'],
            strip_armor(sig)
        )
    else:
        valid = False
    return [valid, sig_info]

### Begin requested functions
# Note: I wasn't sure which address to use to verify the signature, so I used
# the one that is included within the signature. I've left a line of code
# commented marked '#1' that will check if the address in the signature is the
# same as the address in the message
def validate_enrollment(enrollment_signature_text):
    a = verify_sig(enrollment_signature_text)
    # if a[1]['master'] != a[1]['Master signing address']: a[0] = False #1
    if a[0] != False:
        return [a[0], a[1]['master']]
    else:
        return False

def validate_review(reviewer_text):
    a = verify_sig(reviewer_text)
    # if a[1]['master'] != a[1]['Master signing address']: a[0] = False #1
    return [
        a[0],
        a[1]['master'],
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
        a[1]['master'],
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
