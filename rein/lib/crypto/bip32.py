from bip32utils import BIP32Key
from hashlib import sha256, sha512
from binascii import hexlify
from pbkdf2 import PBKDF2
from os import urandom
from unicodedata import normalize
import json
import hmac

# TODO Make Python index this file automatically
WORDS_FILE = 'rein/lib/crypto/resources/english.json'


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
    key = BIP32Key(secret=secret, chain=chain, depth=0, index=0, fpr=b'\0\0\0\0', public=False, testnet=False)
    return key


def get_child_key(parent, depth):
    return parent.ChildKey(depth)


def get_delegate_key(mxprv):
    master_key = get_child_key(mxprv, 1 + 0x80000000)
    delegate_key = get_child_key(master_key, 0)
    return delegate_key


def get_master_address(mxprv):
    master_key = get_child_key(mxprv, 0)
    master_key.SetPublic()
    return master_key.Address()


def get_delegate_address(mxprv):
    delegate_key = get_delegate_key(mxprv)
    delegate_key.SetPublic()
    return delegate_key.Address()


def get_delegate_private_key(mxprv):
    delegate_key = get_delegate_key(mxprv)
    return delegate_key.PrivateKey()


def get_delegate_extended_key(mxprv):
    delegate_key = get_delegate_key(mxprv)
    return delegate_key.ExtendedKey()
