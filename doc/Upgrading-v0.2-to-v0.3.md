# How to upgrade from a previous version of Rein.

tl;dr You will need to create a new identity for Rein v0.3.

If you've been using Rein from before v0.3, your account was created by manually generating a couple of Bitcoin address/private key pairs. With this version we are introducing bip32-based keys. Everything including the master and delegate addresses are generated from a 12-word passphrase. This lays the groundwork for better encryption and privacy going forward. 

If you have setup an identity previously, you will want to complete any jobs you had in-process, then upgrade and generate a new identity.
