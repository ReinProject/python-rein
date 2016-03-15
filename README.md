## Python-Rein

Rein is a new experiment in decentralized markets. Thus far, decentralized markets have built their own p2p networks or stored data in the Blockchain. The Rein model mirrors that of internet at large with paid microhosting. Since storage and bandwidth requirements are low, a high amount of redundancy and censorship-resistance may be acheived at low cost (on par with the cost of a gourmet coffee for a year of redundant hosting on several servers).

This is very much a minimum viable product. Servers don't charge for their services, or sync with each other, and while the client attempts to validate what it sees, this validation is not complete nor has the software seen a security review. As such, you are advised to limit use of Rein to small jobs where loss of funds or time spent would not present a significant burden.

To read more about the project, visit http://reinproject.org

Python-rein is a command-line interface to the Rein decentralized professional services market.

## Installation

Development:

    pip install --editable .

With the --editable switch, your edits immediately become live in your environment.

Production:

    python setup.py install


## Getting started

Setup your identity with:

    rein setup

During the setup process you will enter your name/username, email or BitMessage address, master Bitcoin address, delegate Bitcoin address, and delegate private key. The enrollment, a document storing your initial user information, will need to be signed with the [Bitcoin Signature Tool](https://github.com/ReinProject/bitcoin-signature-tool) which you should download for offline use. Once signed, the enrollment will be stored in the local database for later upload.

Next, you will register (hopefully several) servers with your client. This is done with the _request_ command which is meant to ask for free microhosting (for a limited time only). ReinProject.org is running two such servers. Register them with your client like so:

    rein request http://rein1-sfo.reinproject.org
    rein request http://rein2-ams.reinproject.org

Upload your enrollment with the _sync_ command which puts each document you produce on each server it knows about.

    rein sync

Though some commands request data, none of them upload anything automatically. This means running _rein sync_ is necessary if you want to post anything where others can see it.

### Mediators

Each transaction in Rein requires a job creator, worker, and mediator. Most of the time it is expected that the mediator will do nothing but collect a small fee. In case of dispute, however, the mediator holds a third key so that escrowed funds can be refunded, split or awarded according to their judgement.

### Workers

    rein bid

This command will query each registered server for jobs that are open for bids, and help you build and sign a bid document.

### Job creators

The first step in posting a job is to carefully choose a mediator. At this time there is little in the way of reputation in the system. Your own research should guide your choice.

    rein post

Once a mediator is chosen, you will describe what you want done and by when. Once the post is signed, use sync to push it to your registered servers.

### The rest of the order flow

After a job posting and bids have been made, the job creator will use _offer_ to choose a bid. They should then fund both the primary and mediator escrow addresses so the worker can begin. Once the work is complete, the worker uses _deliver_ to post deliverables which can be reviewed and accepted by the job creator with _accept_. During the _accept_ step, the job creator will be prompted for signed primary and mediator payment transactions. 

Python-rein currently cannot query for unspent outputs or assemble transactions so it is recommended that you download a copy of [ReinProject's fork of Coinb.in](https://github.com/ReinProject/coinbin) in order to sign (and for the worker and mediator, broadcast) the payment transactions.

If you want detailed information about pending jobs use `rein status`. If run with the --jobid option, all documents associated with a specific gig will be printed to the screen.

## Addresses and Payments

Rein uses two types of escrow in order to protect funds that are to go to the worker or job creator (depending upon the success of the transaction) as well as the mediator. 

### Primary payment

For the primary payment, a simple 2-of-3 escrow address is created. To spend the funds placed at this address requires that two parties out of the job creator, worker, and mediator sign each payment. The user is prompted for a signed primary payment if they are a job creator accepting a delivery or they are the mediator resolving a dispute. This payment can be built and signed using Coinb.in which will retrieve unspent outputs (i.e. the funds) and allow the user to specify the destination address and amount, with excess going to the Bitcoin network as a fee for the miner of the transaction. 

Having only been signed by one party, this payment should be reviewed before the second party adds their signature and broadcasts the transaction.

For example in a normal, non-disputed transaction the worker should check that their address is the one being paid that the Bitcoin network fee is reasonable. If an error is found, the signing party can be contacted to build a new transaction with the correct information.

### Mediator payment

For the mediator payment, a mandatory multisig address is created. To spend the funds placed at this address, the mediator must sign the payment and be accompanied by either the job creator or worker's signature. This ensures that the job creator and worker cannot conspire to steal the mediator payment, even though in theory they could both refuse to sign the mediator's payment if both feel the mediator made an unfair judgement.

Like with the primary payment, a user is prompted for a signed mediator payment if they are a job creator accepting a delivery or they are the mediator resolving a dispute.

## Testing

To help test, download and run [a server](https://github.com/ReinProject/causeway) locally. Run `rein testnet true`, then `rein setup`. You can use the address/key pairs on [this sheet](https://docs.google.com/spreadsheets/d/1IRDvu-24LCDOTM1B3lwW9cfQM-zSCK1eds5Sb4QhpWY/edit#gid=691104568) for convenience to setup Alice, Bob, and Charlie with the right keys/identities. 

Then run using nose:

    $ nosetests
    ..
    ----------------------------------------------------------------------
    Ran 2 tests in 0.837s

    OK

Tox fails right now but does run flake so will be helpful for cleanup.
