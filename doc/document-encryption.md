## [Draft] Document Encryption

Each time a worker bids, he encrypts to the client and establishes the shared secret that would be used to encrypt all communications for that job (might get tricky with three parties including mediator), also new addresses are generated from the wallet, a process which could be deterministic.

Each time a client posts a job, he signs the message with his public key. Right now this is just the public key corresponding to the Bitcoin address but this should be hardened by using more bits for the private key part (we should check that 32 byte ECC key is only equivalent to a 3072 bit RSA key). One possible options is to use the chain code part of the extended key from BIP32.

If a worker bids, he encrypts the message to that public key and gives the Diffie-Hellman parameters and a temporary public key for establishing the communications channel.

If the client accepts, he will use the same Diffie-Hellman parameters and give out a temporary public key, so that a shared secret can be created with these two temporary public keys. (x,y) = d_W Q_C = d_C Q_W (see https://en.wikipedia.org/wiki/Elliptic_curve_Diffie%E2%80%93Hellman). This shared secret is the key used for the symmetric encryption algorithm. The proposed system would use serpent-xts-plain64 with 512 bit key sizes and SHA512 for message digest. Using this symmetric encryption the client can broadcast the offer document with a redeem script generated using a fresh public key for the client and the publicly-listed public keys for the worker and mediator.

Mediators do not need to see anything unless he is called for in a dispute document. Whoever creates the dispute document, encrypts the message to the mediators public key and gives the temporary public key and Diffie-Hellman parameters as the worker did.

Once the symmetric encryption shared secret is established between two parties, they use that shared secret to encrypt their messages until the job is done.

Note: When client delivers, he specifies a fresh output address that was generated using BIP32, with the generator public key not known to anyone else.

Another key point is that the establishment of the shared secret should not be spread to other servers, a permanent record would allow third parties to review the records and match shared secrets with public keys.

To be clear: The shared secret can't be decrypted just by seeing the key exchange, but in general it's better to just record what's needed to defend against future quantum computing-based attacks. 
Though it can’t be enforced, all servers should delete any message that they no longer need to broadcast (i.e. once the receiving party gets and stores the message in their client).
