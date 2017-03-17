# How To Setup Rein

## Introduction

Rein is a new decentralized labor market that provides a safe and easy way to earn Bitcoin and to obtain services from professionals globally. It simplifies the process of entering into a digitally-signed contract and behaving honestly to get what you want whether that's work or money. Currently, as Rein is in beta and the process requires use of a command line client. However, the software is easy to install and we appreciate your feedback to help make it easier.

In this tutorial, we will show you how to install the software, setup your account, and get connected.

## Time to complete

3-5 minutes

## Prerequisites

Before following this tutorial, you'll need a few things.

You should have Python 2.7 with pip installed on your computer and be reasonably certain that the computer is free of malware.

You should also have Python's setuptools and flask packages installed.

    sudo pip install setuptools flask

You should have a flash drive or two and a piece of paper. These will be used to save copies of the seed, a list of words that can be used to recover your identity should your computer be compromised or your data lost.

Once you have all of the prerequisites out of the way, let's move on to installing the python-rein client.

## Step 1 -- Install python-rein

The first step in using Rein is to install python-rein on your computer.

### Download the software    

Let's download `python-rein` now from one of these links:

 * [Download (reinproject.org)](https://reinproject.org/bin/latest)
 * [Download (github)](https://github.com/ReinProject/python-rein/archive/v0.3.0-beta.zip)

Unzip this into folder python-rein.

You should now have a copy of the `python-rein` repository in ~/python-rein

### Install the client

Before installing, change to the `python-rein` directory:

    $ cd python-rein

We can now install it with this command:

    $ sudo python setup.py install

With rein installed, we can easily check if it is setup correctly by running it.

    $ rein
    
This should display a page of help text showing lots of commands.

You can use --help with any of the commands to get more information; for example:

    $ rein setup --help

##Step 2 -- Create Your Account

Let's create your Rein user account.

    $ rein start
    
You should see a web form to fill out. Note that all of the information displayed during setup will become public and is available to all users once pushed to a server. Private keys are kept locally and are never shared or sent to servers.

Choose whether you want to be a mediator or not and set your fee. For example, if you put 3% here, you would earn 0.003 BTC for mediating a 0.1 BTC transaction, whether you need to resolve a dispute or not. Click next.

Now you are presented with an ordered list of words that define your identity, called a mnemonic seed. Write these down and put a copy of the words, possibly encryted, onto a thumb drive or two. 

It is NOT advisable to save these words to your computer. If you think of these as cold storage for your identity, Rein generates a hot wallet for day-to-day use that is saved to your computer.

The next screen will require that you type certain words from the seed in to confirm that you have written them down. Click next.

## Step 3 -- Enable Tor (optional)

Privacy is an important feature that Rein aims to provide to its users. For users of the [Tor Browser Bundle](https://www.torproject.org), a single command can be run to enable all traffic to be routed through Tor. It's a good idea to do this before connecting to any servers.

    rein tor true

## Step 4 -- Register and Upload Enrollment

Rein uses microhosting servers to share data between its users. Let's connect python-rein to two such servers that are being operated as a community service by our project.

    $ rein request rein1-sfo.reinproject.org:2016
    
You should now have a message saying you have 1 bucket at the above server. Repeat with a second server.

    $ rein request rein2-ams.reinproject.org:2016

Again, a message should confirm that you have 1 bucket at the above server.

If you wish to donate to help pay for these servers, you can get a donation address with the `rein buy` command.

### Upload your account info 

Next, we'll sync your local Rein database which contains only a single document, with the servers we requested in the previous section.

    $ rein sync

This command checks each registered server for the documents we have created locally and uploads any that are incorrect or do not yet exist. In this case, two servers would be checked and neither would have our document, so two uploads would occur.

You are now ready to start using Rein.

To check the status of your account and any transactions you are involved in, run `rein start` and visit http://localhost:5001.

To bid on any available jobs visit: http://localhost:5001/bid

To post a job visit: http://localhost:5001/post

If you have any questions, corrections, or recommendations please post an issue here or submit a pull request.
