import unittest

from rein.lib import bitcoinecdsa
from rein.lib.crypto import bip32


class Bip32Test(unittest.TestCase):

    def test_bip32(self):
        mnemonic_list_initial = [u'correct',u'horse',u'battery',u'staple']
        key = bip32.mnemonic_to_key(mnemonic_list_initial)
        wifkey_master = bip32.get_master_private_key(key)
        address_master = bip32.get_master_address(key)
        wifkey_delegate = bip32.get_delegate_private_key(key)
        address_delegate = bip32.get_delegate_address(key)

        self.assertEqual(
            bitcoinecdsa.privkey_to_address(wifkey_master),address_master)
        self.assertEqual(
            bitcoinecdsa.privkey_to_address(wifkey_delegate),address_delegate)

        mnemonic = "correct horse battery staple"
        mnemonic_list = str(mnemonic).split()
        mnemonic_list_unicode = [s.decode('unicode-escape') for s in mnemonic_list]

        self.assertEqual(mnemonic_list,mnemonic_list_initial)

        key2 = bip32.mnemonic_to_key(mnemonic_list_unicode)
        wifkey_master2 = bip32.get_master_private_key(key2)
        address_master2 = bip32.get_master_address(key2)
        wifkey_delegate2 = bip32.get_delegate_private_key(key2)
        address_delegate2 = bip32.get_delegate_address(key2)

        self.assertEqual(bitcoinecdsa.privkey_to_address(wifkey_master2),address_master2)
        self.assertEqual(bitcoinecdsa.privkey_to_address(wifkey_delegate2),address_delegate2)

        key3 = bip32.mnemonic_to_key(mnemonic.decode('unicode-escape'))
        wifkey_master3 = bip32.get_master_private_key(key3)
        address_master3 = bip32.get_master_address(key3)
        wifkey_delegate3 = bip32.get_delegate_private_key(key3)
        address_delegate3 = bip32.get_delegate_address(key3)

        self.assertEqual(bitcoinecdsa.privkey_to_address(wifkey_master3),address_master3)
        self.assertEqual(bitcoinecdsa.privkey_to_address(wifkey_delegate3),address_delegate3)
