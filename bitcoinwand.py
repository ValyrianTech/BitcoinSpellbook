#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import os
import sys
import requests
import ipfsapi

from helpers.BIP44 import set_testnet
from helpers.configurationhelpers import get_use_testnet, get_ipfs_host, get_ipfs_port
from helpers.hotwallethelpers import get_private_key_from_wallet, find_address_in_wallet
from sign_message import sign_message
from validators.validators import valid_address

set_testnet(get_use_testnet())


# Create main parser
parser = argparse.ArgumentParser(description='Bitcoin Wand command line interface', formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument('address', help='The address that is sending the message')
parser.add_argument('message', help='The message itself OR name of the file that contains the message')
parser.add_argument('url', help='The url to send the request to')

# Parse arguments
args = parser.parse_args()

# Check if address is valid
if not valid_address(args.address):
    print >> sys.stderr, 'Invalid address: %s' % args.address
    sys.exit(1)

data = {'address': args.address}

# Find the private key of the address in the hot wallet
account, index = find_address_in_wallet(address=data['address'], accounts=5)
if account is None or index is None:
    print >> sys.stderr, 'Can not find address in wallet!'
    sys.exit(1)
else:
    private_key = get_private_key_from_wallet(account=account, index=index)[data['address']]

# If the message argument is the name of an existing file, then the real message is the contents of that file
if os.path.isfile(args.message):
    with open(args.message, 'r') as input_file:
        data['message'] = input_file.read()
else:
    data['message'] = args.message


# The Bitcoin Signed Message can not be longer than 256 characters, if it is longer, put the message on IPFS and sign the hash instead
if len(data['message']) >= 256:
    # Check if IPFS node is running
    try:
        ipfs = ipfsapi.connect(get_ipfs_host(), get_ipfs_port())
    except Exception as ex:
        print 'IPFS node is not running: %s' % ex
        sys.exit(1)

    message_hash = ipfs.add_json(data['message'])
    data['message'] = 'IPFS=%s' % message_hash


# Calculate the signature
data['signature'] = sign_message(address=data['address'], message=data['message'], private_key=private_key)

# Send the signed message as a POST request to the url
try:
    r = requests.post('{url}'.format(url=args.url), json=data)
    print r.text
except Exception as ex:
    print >> sys.stderr, 'Unable to send signed message to trigger: %s' % ex
    sys.exit(1)