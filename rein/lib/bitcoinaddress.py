from hashlib import sha256
from crypto.util import ripemd160
from bitcoin import base58
from binascii import unhexlify
import unittest

digits58 = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'


def to_bytes(n, length, endianess='big'):
    h = '%x' % n
    s = ('0' * (len(h) % 2) + h).zfill(length * 2).decode('hex')
    return s if endianess == 'big' else s[::-1]


def decode_base58(bc, length):
    n = 0
    for char in bc:
        n = n * 58 + digits58.index(char)
    return to_bytes(n, length, 'big')


def check_bitcoin_address(bc):
    if len(bc) < 30:
        return False
    bcbytes = decode_base58(bc, 25)
    return bcbytes[-4:] == sha256(sha256(bcbytes[:-4]).digest()).digest()[:4]


class BitcoinAddressTest(unittest.TestCase):
    def test_check_bitcoin_address(self):
        self.assertTrue(check_bitcoin_address('1CptxARjqcfkVwGFSjR82zmPT8YtRMubub'))
        self.assertTrue(check_bitcoin_address('3746f7fjJ6fG1pQXDjA8xy9WAzf4968WWv'))
        self.assertFalse(check_bitcoin_address('2746f7fjJ6fG1pQXDjA8xy9WAzf4968WWv'))

    def check_sin(self):
        self.assertEqual(sin_type_2('02F840A04114081690223B7069071A70D6DABB891763B638CC20C7EC3BD58E6C86', 'TfG4ScDgysrSpodWD4Re5UtXmcLbY5CiUHA'))

def generate_sin(master_key):
    """Generates a type 2 'Secure Identity Number' using the bip32 master public key"""
    prefix = 0x0F
    sin_type = 0x02
    # Convert master key to hex if necessary
    try:
        master_key = unhexlify(master_key)

    except TypeError:
        pass

    # Step 1 (SHA-256 of public key)
    step_1 = sha256(master_key).hexdigest()
    # Step 2 (RIPEMD-160 of Step 1)
    step_2 = ripemd160(unhexlify(step_1))
    # Step 3 (Prefix + SIN_Version + Step 2)
    step_3 = '{0:02X}{1:02X}{2}'.format(prefix, sin_type, step_2)
    # Step 4 (Double SHA-256 of Step 3)
    step_4_1 = unhexlify(step_3)
    step_4_2 = sha256(step_4_1).hexdigest()
    step_4_3 = unhexlify(step_4_2)
    step_4 = sha256(step_4_3).hexdigest()
    # Step 5 (Checksum), first 8 characters
    step_5 = step_4[0:8]
    # Step 6 (Step 5 + Step 3)
    step_6 = step_3 + step_5
    # Base58-encode to receive final SIN
    sin = base58.encode(unhexlify(step_6))

    return sin