from hashlib import new

def ripemd160(string):
	h = new('ripemd160')
	h.update(string)
	return h.hexdigest()