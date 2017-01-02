from bitcoin import SelectParams
from bitcoin.core import b2x, lx, COIN, COutPoint, CMutableTxOut, CMutableTxIn, CMutableTransaction, Hash160, x
from bitcoin.core.script import CScript, OP_DUP, OP_HASH160, OP_EQUALVERIFY, OP_CHECKSIG, SignatureHash, SIGHASH_ALL, OP_2, OP_3, OP_CHECKMULTISIG, OP_0
from bitcoin.core.scripteval import VerifyScript, SCRIPT_VERIFY_P2SH
from bitcoin.wallet import CBitcoinAddress, CBitcoinSecret
import urllib2, urllib
import json
from hashlib import sha256
api = "blocktrail" #handle this
from .bucket import Bucket
from .io import safe_get

def unspent_txins(address,testnet):
    if (api == "blockr"):
        if testnet:
            url = "https://tbtc.blockr.io/api/v1/address/unspent/"+str(address)
        else:
            url = "https://btc.blockr.io/api/v1/address/unspent/"+str(address)
        hdr = {'User-Agent': 'Mozilla/5.0'}
        request = urllib2.Request(url,headers=hdr)
        response = urllib2.urlopen(request)
        json_object = json.load(response)
        total_value = 0;
        txins = [];
        for tx in json_object['data']['unspent']:
            txid = tx['tx'];
            vout = tx['n'];
            value = float(tx['amount']);
            total_value += value;
            txins.append((txid, vout))
    else:
        if testnet:
            url = "https://api.blocktrail.com/v1/tbtc/address/"+str(address)+"/unspent-outputs?api_key=1e1ebd7ae629e031310ae9d61fe8549c82d0c589"
        else:
            url = "https://api.blocktrail.com/v1/btc/address/"+str(address)+"/unspent-outputs?api_key=1e1ebd7ae629e031310ae9d61fe8549c82d0c589"
        hdr = {'User-Agent': 'Mozilla/5.0'}
        request = urllib2.Request(url,headers=hdr)
        response = urllib2.urlopen(request)
        json_object = json.load(response)
        total_value = 0;
        txins = [];
        for tx in json_object['data']:
            txid = tx['hash'];
            vout = tx['index'];
            value = tx['value']/100000000.;
            total_value += value;
            txins.append((txid, vout))
            
    return (txins,total_value)

def broadcast_tx (tx_hex,rein):

    urls = Bucket.get_urls(rein)
    sel_url = "{0}bitcoin?owner={1}&query=sendrawtransaction&tx={2}&testnet={3}"
    
    for url in urls:
        data = safe_get(rein.log, sel_url.format(url,rein.user.maddr,tx_hex,rein.testnet))
        if data and 'txid' in data:
            print("got data and txid")
            return data['txid']
    
def partial_spend_p2sh (redeemScript,rein):
    daddr = rein.user.daddr
    txin_redeemScript = CScript(x(redeemScript))
    txin_scriptPubKey = txin_redeemScript.to_p2sh_scriptPubKey()
    txin_p2sh_address = CBitcoinAddress.from_scriptPubKey(txin_scriptPubKey)
    (txins,total_value) = unspent_txins(txin_p2sh_address,rein.testnet)
    if len(txins)==0:
        raise ValueError('No unspent txins found')
    txins_str = ""
    txins_obj = []
    for txid,vout in txins:
        txins_str += " "+txid+"-"+str(vout)
        txins_obj.append(CMutableTxIn(COutPoint(lx(txid),vout)))                
    fee = 0.0005
    amount = total_value-fee
    if amount<=0:
        raise ValueError('Not enough value in the inputs')
    txout = CMutableTxOut((total_value-fee)*COIN, CBitcoinAddress(daddr).to_scriptPubKey())
    tx = CMutableTransaction(txins_obj, [txout])
    ntxins = len(txins_obj)
    seckey = CBitcoinSecret(rein.user.dkey)
    sig = "";
    for i in range(0,ntxins):
        sighash = SignatureHash(txin_redeemScript, tx, i, SIGHASH_ALL)
        sig += " "+b2x(seckey.sign(sighash))+"01"
    return (txins_str[1:],str(amount),daddr,sig)

def spend_p2sh (redeemScript,txins_str,amount,daddr,sig,rein):
    txin_redeemScript = CScript(x(redeemScript))
    txin_scriptPubKey = txin_redeemScript.to_p2sh_scriptPubKey()
    txins_obj = []
    for txin_str in txins_str.split():
        txin_list = txin_str.split("-")
        txins_obj.append(CMutableTxIn(COutPoint(lx(txin_list[0]),int(txin_list[1]))))
    txout = CMutableTxOut(amount*COIN,CBitcoinAddress(daddr).to_scriptPubKey())
    tx = CMutableTransaction(txins_obj,[txout])
    seckey = CBitcoinSecret(rein.user.dkey)
    ntxins = len(txins_obj)
    sig_list = []
    for s in sig.split():
        sig_list.append(x(s))
    for i in range(0,ntxins):
        sighash = SignatureHash(txin_redeemScript,tx,i,SIGHASH_ALL)
        sig2 = seckey.sign(sighash)+x("01")
        txins_obj[i].scriptSig = CScript([OP_0, sig2, sig_list[i], txin_redeemScript])
        VerifyScript(txins_obj[i].scriptSig, txin_scriptPubKey, tx, i, (SCRIPT_VERIFY_P2SH,))
    tx_bytes = tx.serialize()
    hash = sha256(sha256(tx_bytes).digest()).digest()
    txid = b2x(hash[::-1])
    txid_causeway = broadcast_tx(b2x(tx_bytes),rein)
    return (txid,sig)

#redeemScript = "522103220d8573c2d9bdea5d60d3ad8a892c94da4a1850445fe3b83b17307a8d655fb1210342b976a71a5aa2daa65512da45f1d44579c1d3fc364d085e398fc771c23fe2622102ba974cf1e3853814e0e05e7e36266e3d5d324eb48a31694d4969bed390535a6053ae"

#(txins_str,amount,daddr,sig) = partial_spend_p2sh(redeemScript,"mgomM45aKPNbjNgq9bs8CnZnMyzNdrv6EB","cMt7JAxa2Uc97yftEomyg4FX5YjgGsNaDF5S165kRiEi5ibQqKot")

#print(spend_p2sh(redeemScript,txins_str,float(amount),daddr,sig,"cUtVwDQqPn75KjnF5Qa3kyVUQmE4gprami3QW1QughTACnkHQHpa"))


