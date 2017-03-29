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

def generate_new_payment_address(dxprv,i):
    parent_key = get_child_key(dxprv, 0+BIP32_HARDEN)
    subparent_key = get_child_key(parent_key,i)
    target_key = get_child_key(parent_key,0)
    return target_key.Address()

def generate_new_escrow_pubkey(dxprv,i):
    parent_key = get_child_key(dxprv, 1+BIP32_HARDEN)
    subparent_key = get_child_key(parent_key,i)
    target_key = get_child_key(parent_key,0)
    return target_key.Address()
