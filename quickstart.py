#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from ConfigParser import ConfigParser
from helpers.jsonhelpers import load_from_json_file
from authentication import initialize_api_keys_file

PROGRAM_DIR = os.path.abspath(os.path.dirname(__file__))

configuration_file = os.path.join(PROGRAM_DIR, 'configuration', 'spellbook.conf')

config = ConfigParser()
if not os.path.isfile(configuration_file):
    config.read(os.path.join(PROGRAM_DIR, 'configuration', 'example_configuration_file.conf'))
else:
    config.read(os.path.join(PROGRAM_DIR, 'configuration', 'spellbook.conf'))


# RESTAPI settings
current_host = config.get(section='RESTAPI', option='host')
host = raw_input('Enter the IP address of the server or press enter to keep the current value (%s) ' % current_host) or current_host
config.set(section='RESTAPI', option='host', value=host)

current_port = config.get(section='RESTAPI', option='port')
port = raw_input('Enter the port of the server or press enter to keep the current value (%s) ' % current_port) or current_port
config.set(section='RESTAPI', option='port', value=port)


# Authentication settings
api_keys_file = os.path.join(PROGRAM_DIR, 'json', 'private', 'api_keys.json')
if not os.path.isfile(api_keys_file):
    print('Initializing api keys')
    initialize_api_keys_file()

api_keys = load_from_json_file(filename=api_keys_file)

current_key = api_keys.keys()[0]
key = raw_input('Enter the API key or press enter to keep the current value (%s) ' % current_key) or current_key
config.set(section='Authentication', option='key', value=key)

current_secret = api_keys[key]['secret']
secret = raw_input('Enter the API secret or press enter to keep the current value (%s) ' % current_secret) or current_secret
config.set(section='Authentication', option='secret', value=secret)


# Wallet settings
current_wallet_dir = config.get(section='Wallet', option='wallet_dir')
wallet_dir = raw_input('Enter the directory for the hot wallet or press enter to keep the current value (%s) ' % current_wallet_dir) or current_wallet_dir
config.set(section='Wallet', option='wallet_dir', value=wallet_dir)

current_default_wallet = config.get(section='Wallet', option='default_wallet')
default_wallet = raw_input('Enter the name of the hot wallet or press enter to keep the current value (%s) ' % current_default_wallet) or current_default_wallet
config.set(section='Wallet', option='default_wallet', value=default_wallet)

current_use_testnet = config.get(section='Wallet', option='use_testnet')
use_testnet = raw_input('Enter if the wallet should use testnet or press enter to keep the current value (%s) ' % current_use_testnet) or current_use_testnet
config.set(section='Wallet', option='use_testnet', value=use_testnet)


# Transactions settings
current_minimum_output_value = config.get(section='Transactions', option='minimum_output_value')
minimum_output_value = raw_input('Enter the minimum output value or press enter to keep the current value (%s) ' % current_minimum_output_value) or current_minimum_output_value
config.set(section='Transactions', option='minimum_output_value', value=minimum_output_value)

current_max_tx_fee_percentage = config.get(section='Transactions', option='max_tx_fee_percentage')
max_tx_fee_percentage = raw_input('Enter the maximum tx fee percentage or press enter to keep the current value (%s) ' % current_max_tx_fee_percentage) or current_max_tx_fee_percentage
config.set(section='Transactions', option='max_tx_fee_percentage', value=max_tx_fee_percentage)


# Apps settings
current_app_data_dir = config.get(section='APPS', option='app_data_dir')
app_data_dir = raw_input('Enter the directory for the app data or press enter to keep the current value (%s) ' % current_app_data_dir) or current_app_data_dir
config.set(section='APPS', option='app_data_dir', value=app_data_dir)


# SMTP settings
current_enable_smtp = config.get(section='SMTP', option='enable_smtp')
enable_smtp = raw_input('Would you like to enable SMTP? (current=%s): ' % current_enable_smtp) or current_enable_smtp
enable_smtp = 'true' if enable_smtp in ['true', 'True', True, 'Yes' 'yes', 'y', 'Y'] else 'false'
config.set(section='SMTP', option='enable_smtp', value=enable_smtp)


if config.getboolean(section='SMTP', option='enable_smtp') is True:
    current_from_address = config.get(section='SMTP', option='from_address')
    from_address = raw_input('Enter the FROM address for sending emails or press enter to keep the current value (%s) ' % current_from_address) or current_from_address
    config.set(section='SMTP', option='from_address', value=from_address)

    current_host = config.get(section='SMTP', option='host')
    host = raw_input('Enter the host address of the SMTP server or press enter to keep the current value (%s) ' % current_host) or current_host
    config.set(section='SMTP', option='host', value=host)

    current_port = config.get(section='SMTP', option='port')
    port = raw_input('Enter the port of the SMTP server or press enter to keep the current value (%s) ' % current_port) or current_port
    config.set(section='SMTP', option='port', value=port)

    current_user = config.get(section='SMTP', option='user')
    user = raw_input('Enter the username for the SMTP server or press enter to keep the current value (%s) ' % current_user) or current_user
    config.set(section='SMTP', option='user', value=user)

    current_password = config.get(section='SMTP', option='password')
    password = raw_input('Enter the password for the SMTP server or press enter to keep the current value (%s) ' % current_password) or current_password
    config.set(section='SMTP', option='password', value=password)


# IPFS settings
current_enable_ipfs = config.get(section='IPFS', option='enable_ipfs')
enable_ipfs = raw_input('Would you like to enable IPFS? (current=%s): ' % current_enable_ipfs) or current_enable_ipfs
enable_ipfs = 'true' if enable_ipfs in ['true', 'True', True, 'Yes' 'yes', 'y', 'Y'] else 'false'
config.set(section='IPFS', option='enable_ipfs', value=enable_ipfs)

if config.getboolean(section='IPFS', option='enable_ipfs') is True:
    current_host = config.get(section='IPFS', option='host')
    host = raw_input('Enter the IP address of the IPFS server or press enter to keep the current value (%s) ' % current_host) or current_host
    config.set(section='IPFS', option='host', value=host)

    current_port = config.get(section='IPFS', option='port')
    port = raw_input('Enter the port of the IPFS server or press enter to keep the current value (%s) ' % current_port) or current_port
    config.set(section='IPFS', option='port', value=port)


with open(configuration_file, 'w') as output_file:
    config.write(output_file)
    print('spellbook.conf file updated')

print("")
print("Don't forget to initialize the hot wallet before starting the spellbookserver")
print("use command: ./hot_wallet.py set_bip44 <your 12 or 24 mnemonic words>")
print("")
print("To start the server, use command: ./spellbookserver.py")
print("")
