#!/usr/bin/env bash

# delete the sqlite db

# setup Bob
rein setup 
rein request
rein sync

# setup Alice who chooses to be a mediator
rein setup --multi
rein request --multi --identity Alice
rein sync --multi --identity Alice

# setup Charlie
rein setup --multi
rein request --multi --identity Charlie
rein sync --multi --identity Charlie

# Bob posts the software job
rein post

# Bob posts the graphics job and pushes both
rein post
rein sync

# Charlie bids on both software jobs
rein bid --multi --identity 
rein bid --multi --identity
rein sync --multi --identity

# Bob creates an offer, and recieves instructions to deposit x amount
rein offer
rein offer
rein sync

# Charlie delivers on the software job
rein deliver --multi --identity

# Bob accepts the delivery
rein accept

# Bob disputes on the graphics job
rein creatordispute

# Charlie disputes on the graphics job
rein workerdispute --multi

# Alice decides for Bob
rein resolve --multi --identity
