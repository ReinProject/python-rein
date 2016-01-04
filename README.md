# Python-Rein

Python command line interface to the Rein decentralized professional services market.

# Installation

For development:

    pip install --editable .

The --editable flag makes your edits to these files live immediately in your environment.

For production (where data and happiness are produced) use this instead:

    python setup.py install

# Testing

To help test, download and run [the server](https://github.com/weex/playground21/causeway) on port 5000. Run 'rein setup'. You can use the address/key pairs on [this sheet](https://docs.google.com/spreadsheets/d/1IRDvu-24LCDOTM1B3lwW9cfQM-zSCK1eds5Sb4QhpWY/edit#gid=691104568) for convenience. Then run 'rein request localhost:5000' and 'rein sync' to try to store the enrollment message you signed on your Causeway server.

# Usage

    rein --help

