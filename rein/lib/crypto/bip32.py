from bip32utils import BIP32Key, BIP32_HARDEN
from hashlib import sha256, sha512
from binascii import hexlify
from pbkdf2 import PBKDF2
from os import urandom
from unicodedata import normalize
import json
import hmac
import os
import rein.lib.config as config
import unittest

# TODO Make Python index this file automatically
script_dir = os.path.dirname(__file__)
WORDS_FILE_rel = 'resources/english.json'
WORDS_FILE = os.path.join(script_dir, WORDS_FILE_rel)

rein = config.Config()

def generate_mnemonic(strength):
    # Generate seed + checksum
    entropy = urandom(strength // 8)
    bin_entropy = bin(int(hexlify(entropy), 16))[2:].zfill(strength)
    checksum = bin(int(sha256(entropy).hexdigest(), 16))[2:].zfill(256)[:4]
    bin_mnemonic = bin_entropy + checksum
    # Binary to words
    cursor = 0
    mnemonic = []
    with open(WORDS_FILE) as words_file:
        words = json.loads(words_file.read())
        while cursor < len(bin_mnemonic):
            index = int(bin_mnemonic[cursor:cursor+11], 2)
            mnemonic.append(words[index])
            cursor += 11
    return mnemonic


def mnemonic_to_key(mnemonic):
    # Mnemonic to seed. No custom passphrase supported
    mnemonic = normalize('NFKD', ' '.join(mnemonic))
    seed = PBKDF2(mnemonic, u'mnemonic', iterations=2048, macmodule=hmac, digestmodule=sha512).read(64)
    # Seed to key
    secret, chain = seed[:32], seed[32:]
    key = BIP32Key(secret=secret, chain=chain, depth=0, index=0, fpr=b'\0\0\0\0', public=False, testnet=rein.testnet)
    return key


def seed_to_key(seed):
    secret, chain = seed[:32], seed[32:]
    key = BIP32Key(secret=secret, chain=chain, depth=0, index=0, fpr=b'\0\0\0\0', public=False, testnet=rein.testnet)
    return key


def get_child_key(parent, depth):
    return parent.ChildKey(depth)


def get_delegate_key(mxprv):
    master_key = get_child_key(mxprv, 1 + BIP32_HARDEN)
    delegate_key = get_child_key(master_key, 0)
    return delegate_key


def get_master_address(mxprv):
    master_key = get_child_key(mxprv, 0)
    master_key.SetPublic()
    return master_key.Address()


def get_master_private_key(mxprv):
    master_key = get_child_key(mxprv, 0)
    return master_key.WalletImportFormat()


def get_delegate_address(mxprv):
    delegate_key = get_delegate_key(mxprv)
    delegate_key.SetPublic()
    return delegate_key.Address()


def get_delegate_private_key(mxprv):
    delegate_key = get_delegate_key(mxprv)
    return delegate_key.WalletImportFormat()


def get_delegate_extended_key(mxprv):
    delegate_key = get_delegate_key(mxprv)
    return delegate_key.ExtendedKey()


class BitcoinAddressTest(unittest.TestCase):
    def test_check_bitcoin_address(self):

        mnemonic_list_initial = [u'correct',u'horse',u'battery',u'staple']
        key = mnemonic_to_key(mnemonic_list_initial)
        wifkey_master = get_master_private_key(key)
        address_master = get_master_address(key)
        wifkey_delegate = get_delegate_private_key(key)
        address_delegate = get_delegate_address(key)

        from rein.lib.bitcoinecdsa import privkey_to_address
        
        self.assertEqual(privkey_to_address(wifkey_master),address_master)
        self.assertEqual(privkey_to_address(wifkey_delegate),address_delegate)

        mnemonic = "correct horse battery staple"
        mnemonic_list = str(mnemonic).split()
        mnemonic_list_unicode = [s.decode('unicode-escape') for s in mnemonic_list]

        self.assertEqual(mnemonic_list,mnemonic_list_initial)
        
        key2 = mnemonic_to_key(mnemonic_list_unicode)
        wifkey_master2 = get_master_private_key(key2)
        address_master2 = get_master_address(key2)
        wifkey_delegate2 = get_delegate_private_key(key2)
        address_delegate2 = get_delegate_address(key2)

        self.assertEqual(privkey_to_address(wifkey_master2),address_master2)
        self.assertEqual(privkey_to_address(wifkey_delegate2),address_delegate2)
        
        key3 = mnemonic_to_key(mnemonic.decode('unicode-escape'))
        wifkey_master3 = get_master_private_key(key3)
        address_master3 = get_master_address(key3)
        wifkey_delegate3 = get_delegate_private_key(key3)
        address_delegate3 = get_delegate_address(key3)
        
        self.assertEqual(privkey_to_address(wifkey_master3),address_master3)
        self.assertEqual(privkey_to_address(wifkey_delegate3),address_delegate3)
