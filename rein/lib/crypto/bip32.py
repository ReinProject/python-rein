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

# ---- Logic ----

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
    return seed_to_key(seed)


def seed_to_key(seed):
    secret, chain = seed[:32], seed[32:]
    key = BIP32Key(secret=secret, chain=chain, depth=0, index=0, fpr=b'\0\0\0\0', public=False, testnet=False)
    return key

# ---- Internal wrappers ----

def get_child_key(parent, depth):
    return parent.ChildKey(depth)


def get_delegate_key(key):
    master_key = get_child_key(key, 1 + 0x80000000)
    delegate_key = get_child_key(master_key, 0)
    return delegate_key


def get_master_address(key):
    master_key = get_child_key(key, 0)
    master_key.SetPublic()
    return master_key.Address()


def get_master_private_key(key):
    master_key = get_child_key(key, 0)
    return master_key.WalletImportFormat()


def get_delegate_address(key):
    delegate_key = get_delegate_key(key)
    delegate_key.SetPublic()
    return delegate_key.Address()


def get_delegate_private_key(key):
    delegate_key = get_delegate_key(key)
    return delegate_key.WalletImportFormat()


def get_delegate_extended_key(key):
    delegate_key = get_delegate_key(key)
    return delegate_key.ExtendedKey()

# ---- UI callable wrapper ----

def get_user_data(key):
    mprv = get_master_private_key(key)
    maddr = get_master_address(key)
    daddr = get_delegate_address(key)
    dkey = get_delegate_private_key(key)
    dxprv = get_delegate_extended_key(key)
    return mprv, maddr, daddr, dkey, dxprv
