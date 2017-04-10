# Key Management in Rein

### Goals:

 * Privacy - Keys involved in a transaction only need to be known by parties to that transaction. 
This means knowing a key that is used to sign a document or payment should not lead to the 
discovery of a user''s other keys.

 * Multilayered security - An identity is defined by a 12-word mnemonic seed that is meant to be kept offline. The seed is used to generate a BIP32 key that serves as the root of an identity. From that tree, delegate payment and signing addresses are generated.

 * Long-term efficiency - Efficient use of BIP32 tree structures should make it possible to use an 
identity long-term without compromising the root key or needing to expend excessive processing power 
to enumerate.

### Current implementation:

 * Root key (m) - Derived from the 12-word mnemonic seed.

 * Master signing key (m/0) - This key is used to sign the primary document defining a user''s identity 
 in Rein, called an enrollment. In includes name, contact info, whether a user is willing to be a 
 mediator in others transactions and their desired fee rate. The enrollment also includes a Secure 
 Identity Number (SIN), generated from the master signing key. This SIN is specified on the Bitcoin 
 wiki as Identity Protocol v1 and used by Bitrated as a unique identifier for a user.

 * Delegate key (m/1''/0) - A delegate key is used for day-to-day signatures of documents like job 
 postings, bids, offers, disputes and is also used for controlling payments.

### Deficiencies with current implementation:

 * Multisig escrows built for a specific client, worker, and mediator always generate the same escrow address. This means funds escrowed for a particular set of participants can get mixed up (e.g. all funds may be sent for the first completed job).

 * The public part of the key used to sign documents must be made available so that others can verify 
 their authenticity. Since this same key is used to generate a user''s payment address meaning all 
 incoming payments and document signatures are trivially linked.
 
### Future directions:

 * Unique public keys per escrow (m/1''/k with k > 0) - A unique key will be generated from the BIP32 tree
 for each post or bid. This key will be used to build escrow addresses and to sign payments at
 conclusion of each job.
 
 * Unique internal wallet address per job (m/0''/k) - A unique payment address will be generated from the
 BIP32 tree for each post or bid. This is where funds will be sent when payments are sent from escrow
 back to a client, to a mediator, or to a freelancer.
