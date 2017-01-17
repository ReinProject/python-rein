## Python-Rein

[![Build Status](https://travis-ci.org/ReinProject/python-rein.svg?branch=master)](https://travis-ci.org/ReinProject/python-rein)

Rein is designed to help you and others work together with Bitcoin. The Rein model of commerce mirrors that of internet at large through the use of paid microhosting to store data about users, jobs, and payments. Since little storage and bandwidth are needed, a high amount of redundancy and censorship-resistance may be acheived at low cost (on par with the cost of a gourmet coffee for a year of redundant hosting on several servers).

Servers can be paid for their services but they do not communicate with each other, and while the client attempts to validate what it sees, this validation is not complete nor has the software seen a security review. As such, you are advised to limit use of Rein to small jobs where loss of funds or time spent would not present a significant burden.

To read more about the project, visit http://reinproject.org

Python-rein is a command-line and under construction web-interface client to the Rein market.

## Installation

Development:

    pip install --editable .

With the --editable switch, your edits immediately become live in your environment.

Production:

    python setup.py install


## Getting started

Please see the [setup guide](https://github.com/ReinProject/python-rein/blob/master/doc/HOWTO-setup-rein.md). In a nutshell, run `rein start` to be guided through a web-based setup process.

### Mediators

Each transaction in Rein requires a job creator, worker, and mediator. Most of the time it is expected that the mediator will do nothing but collect a small fee. In case of dispute, however, the mediator holds a third key refund, split or award escrowed funds using their best judgement.

### Job creators and workers

Run the following command to get started.

    rein start

This will guide you through a setup process and provide a simple interface for you to use Rein. 

### The rest of the order flow

After a job posting and bids have been made, the job creator will use _offer_ to choose a bid. They should then fund both the primary and mediator escrow addresses so the worker can begin. Once the work is complete, the worker uses _deliver_ to post deliverables which can be reviewed and accepted by the job creator with _accept_. During the _accept_ step, the job creator will be prompted for signed primary and mediator payment transactions. 

Python-rein currently cannot query for unspent outputs or assemble transactions so it is recommended that you download a copy of [ReinProject's fork of Coinb.in](https://github.com/ReinProject/coinbin) in order to sign (and for the worker and mediator, broadcast) the payment transactions.

If you want detailed information about pending jobs, click on the job in question after running `rein start`. 

## Addresses and Payments

Rein uses two types of escrow in order to protect funds that are to go to the worker or job creator (depending upon the success of the transaction) as well as the mediator. 

### Primary payment

For the primary payment, a simple 2-of-3 escrow address is created. To spend the funds placed at this address requires that two parties out of the job creator, worker, and mediator sign each payment. The user is prompted for a signed primary payment if they are a job creator accepting a delivery or they are the mediator resolving a dispute. This payment can be built and signed using Coinb.in which will retrieve unspent outputs (i.e. the funds) and allow the user to specify the destination address and amount, with excess going to the Bitcoin network as a fee for the miner of the transaction. 

Having only been signed by one party, this payment should be reviewed before the second party adds their signature and broadcasts the transaction.

For example in a normal, non-disputed transaction the worker should check that their address is the one being paid and that the Bitcoin network fee is reasonable. If an error is found, the signing party can be contacted to build a new transaction with the correct information.

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

There are also some tests that run via unittest2:

    $ make test
    python -m unittest2 rein/lib/*.py
    ....
    ----------------------------------------------------------------------
    Ran 4 tests in 0.001s
    
    OK

Tox fails right now but does run flake so will be helpful for cleanup.
