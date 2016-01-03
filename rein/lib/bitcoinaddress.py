from hashlib import sha256
 
digits58 = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'

def to_bytes(n, length, endianess='big'):
    h = '%x' % n
    s = ('0'*(len(h) % 2) + h).zfill(length*2).decode('hex')
    return s if endianess == 'big' else s[::-1]

def decode_base58(bc, length):
    n = 0
    for char in bc:
        n = n * 58 + digits58.index(char)
    return to_bytes(n, length, 'big')

def check_bitcoin_address(bc):
    bcbytes = decode_base58(bc, 25)
    return bcbytes[-4:] == sha256(sha256(bcbytes[:-4]).digest()).digest()[:4]
                                  
#print(check_bc('1AGNa15ZQXAZUgFiqJ3i7Z2DPU2J6hW62i'))
#print(check_bc("17NdbrSGoUotzeGCcMMCqnFkEvLymoou9j"))
