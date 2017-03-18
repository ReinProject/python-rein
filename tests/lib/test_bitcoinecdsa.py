import unittest

from rein.lib.bitcoinecdsa import pubkey_to_address, privkey_to_address

class TestBitcoinEcdsa(unittest.TestCase):
    def test_pubkey_to_address(self):
        self.assertEqual(pubkey_to_address('029fcafbe2dced6fe79865b265ea90387c5411658ca11449999d5020a9f67bb005'),
                                           '19skaV7ZDvSe2zKXB32fcay2NzajJcRG8B')
        self.assertNotEqual(pubkey_to_address('029fcafbe2dced6fe79865b265ea90387c5411658ca11449999d5020a9f67bb005'),
                                              '1LgubGW1vZFkR79tZtuDU5jk4DqagDgUih')

    def test_privkey_to_address(self):
        self.assertFalse(privkey_to_address('notaprivkey'))
        self.assertEqual(privkey_to_address('KwKnhdiSmGiCkWneqyFZEDcD2NftCyqRFz7U96dq8BYudkXMCTtJ'),
                                            '12YFs9A39J8npGUvZZ6Mune3mCwrJ6Gky1')
        self.assertNotEqual(privkey_to_address('KwKnhdiSmGiCkWneqyFZEDcD2NftCyqRFz7U96dq8BYudkXMCTtJ'),
                                               '1LgubGW1vZFkR79tZtuDU5jk4DqagDgUih')
