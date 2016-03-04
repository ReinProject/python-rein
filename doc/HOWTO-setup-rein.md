#How To Setup Rein to Start Earning Bitcoin

##Introduction

Rein is a new decentralized labor market that provides a safe and easy way to earn Bitcoin and to obtain services from professionals globally. It simplifies the process of entering into a digitally-signed contract and behaving honestly to get what they want. Currently, as Rein is still in alpha, the process requires use of a command line client. However, the software is easy to install with commands that make sense once you've seen them in action.

In this tutorial, we will show you how to use Rein to earn Bitcoin online. We will also show you how to generate a couple of standalone Bitcoin keys that will form the basis of your user account in Rein.

## Time to complete

10-20 minutes

##Prerequisites

Before following this tutorial, you'll need a few things.

You should have Python 2.7 with pip installed on your computer and be reasonably certain that the computer is free of malware.

You should also have Bitcoin Core installed. It's not required that it be sync'd to the blockchain for this HOWTO. We'll be using it to generate addresses but to be able to detect payments and spend your earnings, you will want to sync it up later.

You should have a way to boot into a GNU+Linux Live CD environment. Perhaps by using unetbootin and the latest Ubuntu ISO with a thumb drive.

You should have a few flash drives onto which you will backup a Bitcoin wallet.

Once you have all of the prerequisites out of the way, let's move on to installing the python-rein client and helper apps.

##Step 1 -- Install python-rein and helper apps

The first step in using Rein to earn Bitcoin is to install the python-rein software on your computer. Currently, the best way to install python-rein is simply to clone it from the Github repository. In the future, it will likely be available through your package manager.

###Clone the repo    

Let's clone `python-rein` now into your home folder with this command:

    $ git clone https://github.com/ReinProject/python-rein.git ~/python-rein

You should now have a copy of the `python-rein` repository in ~/python-rein

###Install the client

Before installing, change to the `python-rein` directory:

    $ cd python-rein

We can now install `python-rein` with this command:

    $ pip install --editable .

With rein installed, we can easily check if it is setup correctly by running it.

    $ rein
    
This should display a page of help text showing lots of commands. You can use --help with any of the commands to get more information.

###Download the helper apps

To help you make digital signatures the bitcoin-signature-tool and a modified version of Coinbin have been built for Rein.

    $ cd 
    $ mkdir Rein && cd Rein
    $ git clone https://github.com/ReinProject/bitcoin-signature-tool.git
    $ git clone https://github.com/ReinProject/coinbin.git

You should now have the bitcoin-signature-tool and Coinbin for Rein to help make signatures with Bitcoin ECDSA private keys.

##Step 2 -- Prepare a Bitcoin Wallet

Rein provides the ability to have as many identities as you would like, though for anything where trust and reputation are important, you will probably want to transact through your main identity. These identities are defined by a Bitcoin ECDSA keypair (i.e. an address) which we call the identity's master address. 

In this setup, we'll show you how to use **Bitcoin Core** to generate Bitcoin addresses and save their private keys for convenient use later.

###Create an encrypted Bitcoin Wallet

Bitcoin Core provides a very simple way to create Bitcoin addresses. When the program `bitcoin-qt` is opened for the first time, it generates a wallet automatically. This wallet can then be encrypted to protect against theft and copies of the wallet can be backed up to removable media.

Before we obtain any addresses, let's encrypt the wallet.

<img src="http://reinproject.org/img/encrypt.png">

Enter a strong password of at least 10 characters. It is **very important** that you have this password when you need access in the future so put it in your password manager, write it down, and/or memorize it. If you lose the password or the wallet file, you will lose access to any Rein identities and Bitcoin funds for which it holds the keys.

###Backup the Wallet

Make a few backup copies of the wallet to removable media such as flash drives, memory cards, or optical media. Ideally you will store these in a safe or safe deposit box.

<img src="http://reinproject.org/img/backup.png">

##Step 3 -- Create Your User Account

Let's create your Rein user account, also known in the software as an identity.

    $ rein setup
    
Choose to create a new account, fill in your Name or the handle by which you'd to attach to the identity and an email or BitMessage address that can be used to contact you. Note that all of the information in your setup except the private keys will become public so use an email address with good spam protection or BitMessage which has spam protection included.

###Obtain address from Bitcoin-Qt

<img src="http://reinproject.org/img/rein-enroll.png">

Let's obtain the Master Bitcoin address from Bitcoin-Qt. Here you will go to File -> Receiving Addresses... and click new until there are a couple of addresses showing. Copy the first address and paste it here.

Next, we'll get a different address from Bitcoin-Qt and copy and paste it at the Delegate Bitcoin address prompt.

<img src="http://reinproject.org/img/rein-enroll2.png">

###Get a private key from Bitcoin-Qt

For the final prompts in rein setup, we will need the private keys for the two above addresses. We'll start by getting the private key from Bitcoin-Qt for the Delegate address.

Open the Debug Window to the Console tab.

<img src="http://reinproject.org//img/debug.png">

There you will type the following command:

    dumpprivkey &lt;your address&gt;

<img src="http://reinproject.org/img/dumpprivkey1.png">

After a second or two, this will print out the private key for the address. 

<img src="http://reinproject.org/img/dumpprivkey2.png">

Copy the private key (redacted) and paste it in for the Delegate Bitcoin private key. You will repeat this process for the Master address but before we do that, let's answer the prompts around being a mediator.

If you choose to be a mediator, you will be prompted for your mediation fee in percent. For example, if you put 5% here, you would earn 0.05 BTC for mediating a 1 BTC transaction, whether you need to resolve a dispute or not.

###Sign the enrollment

You should now have a section of text on the screen that starts with "Rein User Enrollment". To finish creating your user account, we'll sign this text using the Bitcoin Signature Tool.

Open your browser and open the file at ~/Rein/bitcoin-signature-tool/index.html. Click over to the Sign tab and repeat the above procedure to get the private key for your Master Bitcoin address.

<img src="http://reinproject.org/img/master-signing.png">

The private key will go in the Private Key box shaded in red. Copy the "Rein User Enrollment" text into the Message box shaded in yellow. 

Click "Sign Message" to generate the signature. A block of text that includes the message and signature will be generated in the green area. Click it to highlight it and copy that text.

Save this text to a plain-text file called enrollment.txt.sig in your ~/python-rein/ directory.

Once this is done, you will complete the account setup by pressing enter back in the terminal window where `rein setup` is running.

Python-rein will check the signature in the text file you just created and if it is valid, will save the entire signed document to its local database. 

We are now ready for the next step, which is to register with some Rein servers.

##Step 3 -- Register and Upload Enrollment

Rein uses microhosting servers to share data between its users. Let's connect python-rein to two such servers, that are being operated as a community service by ReinProject.org.

    $ rein request rein1-sfo.reinproject.org:2016
    
You should now have a message saying you have 1 bucket at the above server. Repeat with a second server.

    $ rein request rein1-ams.reinproject.org:2016

Again, a message should confirm that you have 1 bucket at the above server.

### Upload your Enrollment

Next, we'll sync your local Rein database which contains only a single document, with the servers we `request`-ed in the previous section.

    $ rein sync

This command checks each registered server for the documents we have created locally and uploads any that are incorrect or do not yet exist. In this case, two servers would be checked and neither would have our document, so two uploads would occur.

You are now ready to start earning bitcoin through Rein.

To check the status of your account and any transactions you may be involved in, run `rein status`.

If you are a mediator who must resolve a dispute, you will see a transaction listed in the output. Workers and job creators would also be advised to message you via the information in the Contact section of your enrollment.

For further reference, much of the above process is shown in the video [Rein - Getting started: Install and Setup - part 2/4 ](https://www.youtube.com/watch?v=PaF5URG2dLc)

If you have any questions, corrections, or recommendations please post an issue here or submit a pull request.
