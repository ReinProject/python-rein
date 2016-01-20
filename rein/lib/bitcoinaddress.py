from hashlib import sha256
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
    bcbytes = decode_base58(bc, 25)
    return bcbytes[-4:] == sha256(sha256(bcbytes[:-4]).digest()).digest()[:4]


class BitcoinAddressTest(unittest.TestCase):
    def test_check_bitcoin_address(self):
        self.assertTrue(check_bitcoin_address('1CptxARjqcfkVwGFSjR82zmPT8YtRMubub'))
        self.assertTrue(check_bitcoin_address('3746f7fjJ6fG1pQXDjA8xy9WAzf4968WWv'))
        self.assertFalse(check_bitcoin_address('2746f7fjJ6fG1pQXDjA8xy9WAzf4968WWv'))
