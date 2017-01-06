import click
import bitcoin
from bitcoin.core import b2x, lx, x
from bitcoin.core.script import CScript, OP_CHECKMULTISIG, OP_CHECKSIGVERIFY
from bitcoin.wallet import CBitcoinAddress
from .validate import parse_document
import unittest

def parse_script(text):
    try:
        parsed = bitcoin.core.script.CScript(x(text))
    except:
        pass

    if parsed.is_valid():
        # return as array of strings
        as_array = []
        for i in parsed:
            if isinstance(i, int):
                as_array.append(str(i))
            else:
                as_array.append(b2x(i))
        return as_array
    else:
        return False

def build_2_of_3(pubkeys):
    txin_redeemScript = CScript([2, x(pubkeys[0]), x(pubkeys[1]), x(pubkeys[2]), 3, OP_CHECKMULTISIG])
    txin_scriptPubKey = txin_redeemScript.to_p2sh_scriptPubKey()
    txin_p2sh_address = CBitcoinAddress.from_scriptPubKey(txin_scriptPubKey)
    return (b2x(txin_redeemScript), str(txin_p2sh_address))

def build_mandatory_multisig(mandatory_pubkey, other_pubkeys):
    txin_redeemScript = CScript([x(mandatory_pubkey), OP_CHECKSIGVERIFY, 1, x(other_pubkeys[0]), x(other_pubkeys[1]), 2, OP_CHECKMULTISIG])
    txin_scriptPubKey = txin_redeemScript.to_p2sh_scriptPubKey()
    txin_p2sh_address = CBitcoinAddress.from_scriptPubKey(txin_scriptPubKey)
    return (b2x(txin_redeemScript), str(txin_p2sh_address))

def check_2_of_3(parsed, expected_public_keys):
    if parsed[0] != '2' or parsed[4] != '3' or parsed[5] != 'OP_CHECKMULTISIG':
        click.echo("2 %s,  3 %s, or cms %s failed" % (parsed[0]. parsed[4], parsed[5]))
        return False
    for k in expected_public_keys:
        if k not in parsed:
            print(k + ' not found')
            return False
    if len(parsed) != 6:
        click.echo("bad len %s" % len(parsed))
        return False
    return True


def check_mandatory_multisig(parsed, mandatory_public_key, other_public_keys):
    if parsed[0] != mandatory_public_key:
        return False
    if (parsed[1] != 'OP_CHECKSIGVERIFY'
      or parsed[2] != '1'
      or parsed[5] != '2'
      or parsed[6] != 'OP_CHECKMULTISIG'):
        return False
    for k in other_public_keys:
        if k != parsed[3] and k != parsed[4]:
            print(k + ' not found')
            return False
    if len(parsed) != 7:
        return False
    return True

def check_redeem_scripts(document):
    ret = parse_document(document)
    if u'Primary escrow redeem script' in ret.keys():
        pubkeys = [ret['Job creator public key'], ret['Worker public key'], ret['Mediator public key']]
        if not check_2_of_3(parse_script(ret[u'Primary escrow redeem script']), pubkeys):
            click.echo("2-of-3 check failed")
            return False

    if u'Mediator escrow redeem script' in ret.keys():
        pubkeys = [ret['Job creator public key'], ret['Worker public key']]
        if not check_mandatory_multisig(parse_script(ret[u'Mediator escrow redeem script']),
                                        ret['Mediator public key'], pubkeys):
            click.echo("2-of-3 check failed")
            return False
    return True

class BitcoinScriptTest(unittest.TestCase):
    def test_2_of_3(self):
        # primary payment 2-of-3 redeem script
        p = parse_script('5221029fcafbe2dced6fe79865b265ea90387c5411658ca11449999d5020a9f67bb0052102f719f009fb8eb20ccdbfda7d38f378ed2f103ac0a6768df830740c6835c4651921026bc363139ebc1cad8e6eee402507d2b4874f5450585f1e6a1cd30a63ecdfc9dc53ae')
        self.assertTrue(check_2_of_3(p, ['029fcafbe2dced6fe79865b265ea90387c5411658ca11449999d5020a9f67bb005',
                                         '02f719f009fb8eb20ccdbfda7d38f378ed2f103ac0a6768df830740c6835c46519',
                                         '026bc363139ebc1cad8e6eee402507d2b4874f5450585f1e6a1cd30a63ecdfc9dc']))
        # switch key order
        self.assertTrue(check_2_of_3(p, ['02f719f009fb8eb20ccdbfda7d38f378ed2f103ac0a6768df830740c6835c46519',
                                         '029fcafbe2dced6fe79865b265ea90387c5411658ca11449999d5020a9f67bb005',
                                         '026bc363139ebc1cad8e6eee402507d2b4874f5450585f1e6a1cd30a63ecdfc9dc']))

    def test_mandatory_multisig(self):
        # mandatory multisig for mediator

        m = parse_script('2102f719f009fb8eb20ccdbfda7d38f378ed2f103ac0a6768df830740c6835c46519ad5121029fcafbe2dced6fe79865b265ea90387c5411658ca11449999d5020a9f67bb00521026bc363139ebc1cad8e6eee402507d2b4874f5450585f1e6a1cd30a63ecdfc9dc52ae')
        self.assertTrue(check_mandatory_multisig(m, '02f719f009fb8eb20ccdbfda7d38f378ed2f103ac0a6768df830740c6835c46519',
                                                   ['029fcafbe2dced6fe79865b265ea90387c5411658ca11449999d5020a9f67bb005',
                                                    '026bc363139ebc1cad8e6eee402507d2b4874f5450585f1e6a1cd30a63ecdfc9dc']))
        # switch non-mandatory key order
        self.assertTrue(check_mandatory_multisig(m, '02f719f009fb8eb20ccdbfda7d38f378ed2f103ac0a6768df830740c6835c46519',
                                                   ['029fcafbe2dced6fe79865b265ea90387c5411658ca11449999d5020a9f67bb005',
                                                    '026bc363139ebc1cad8e6eee402507d2b4874f5450585f1e6a1cd30a63ecdfc9dc']))
        # mix up mandatory and non-mandatory keys
        self.assertFalse(check_mandatory_multisig(m, '029fcafbe2dced6fe79865b265ea90387c5411658ca11449999d5020a9f67bb005',
                                                    ['02f719f009fb8eb20ccdbfda7d38f378ed2f103ac0a6768df830740c6835c46519',
                                                     '026bc363139ebc1cad8e6eee402507d2b4874f5450585f1e6a1cd30a63ecdfc9dc']))

    def test_build_redeem_scripts(self):
        self.assertEquals(build_2_of_3(['02f719f009fb8eb20ccdbfda7d38f378ed2f103ac0a6768df830740c6835c46519',
                                        '029fcafbe2dced6fe79865b265ea90387c5411658ca11449999d5020a9f67bb005',
                                        '026bc363139ebc1cad8e6eee402507d2b4874f5450585f1e6a1cd30a63ecdfc9dc'])[0], 
                          '522102f719f009fb8eb20ccdbfda7d38f378ed2f103ac0a6768df830740c6835c4651921029fcafbe2dced6fe79865b265ea90387c5411658ca11449999d5020a9f67bb00521026bc363139ebc1cad8e6eee402507d2b4874f5450585f1e6a1cd30a63ecdfc9dc53ae')

        self.assertEquals(build_mandatory_multisig('02f719f009fb8eb20ccdbfda7d38f378ed2f103ac0a6768df830740c6835c46519',
                                                  ['029fcafbe2dced6fe79865b265ea90387c5411658ca11449999d5020a9f67bb005',
                                                   '026bc363139ebc1cad8e6eee402507d2b4874f5450585f1e6a1cd30a63ecdfc9dc'])[0],
                          '2102f719f009fb8eb20ccdbfda7d38f378ed2f103ac0a6768df830740c6835c46519ad5121029fcafbe2dced6fe79865b265ea90387c5411658ca11449999d5020a9f67bb00521026bc363139ebc1cad8e6eee402507d2b4874f5450585f1e6a1cd30a63ecdfc9dc52ae')
