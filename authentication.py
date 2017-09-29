#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
import simplejson
import random
import string
import hashlib
import hmac
import base64

from jsonhelpers import save_to_json_file, load_from_json_file

LAST_NONCES = {}


class AuthenticationStatus(object):
    OK = 'OK'
    INVALID_API_KEY = 'Invalid API key'
    NO_API_KEY = 'No API key supplied'
    INVALID_SIGNATURE = 'Invalid signature'
    NO_SIGNATURE = 'No signature supplied'
    INVALID_JSON_FILE = 'Invalid json file'
    NO_NONCE = 'No nonce supplied'
    INVALID_NONCE = 'Invalid nonce'


API_KEYS_FILE = 'api_keys.json'


def initialize_api_keys_file():
    """
    Initialize the api_keys.json file with a new random api key and secret for the admin
    """
    # Create a random string of characters (uppercase letters and digits) for a api_key and api_secret pair
    api_key = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(16))
    api_secret = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(16))

    data = {api_key: {'secret': api_secret,
                      'permissions': 'all'}}

    save_to_json_file(API_KEYS_FILE, data)


def check_authentication(headers, data):
    """
    Checks if the headers contain valid authentication information
    This must include the following headers:
    - API_Key: an identifier for the account
    - API_Sign: a signature
    - API_NONCE: an integer, each request must have a nonce that is higher than the nonce of the previous request

    :param headers: The headers of the http request
    :param data: The json data of the http request
    :return: An AuthenticationStatus
    """
    global LAST_NONCES

    api_keys = load_from_json_file(API_KEYS_FILE)
    if api_keys is None:
        return AuthenticationStatus.INVALID_JSON_FILE

    if 'API_Key' not in headers:
        return AuthenticationStatus.NO_API_KEY

    if 'API_Sign' not in headers:
        return AuthenticationStatus.NO_SIGNATURE

    if 'API_Nonce' not in headers:
        return AuthenticationStatus.NO_NONCE

    api_key = headers['API_Key']
    if api_key not in api_keys or 'secret' not in api_keys[api_key]:
        return AuthenticationStatus.INVALID_API_KEY

    try:
        nonce = int(headers['API_Nonce'])
    except Exception as ex:
        return AuthenticationStatus.INVALID_NONCE

    if api_key in LAST_NONCES and LAST_NONCES[api_key] >= nonce:
        return AuthenticationStatus.INVALID_NONCE

    LAST_NONCES[api_key] = nonce

    signature = headers['API_Sign']
    message = hashlib.sha256(str(nonce) + simplejson.dumps(data, sort_keys=True, indent=2)).digest()
    if signature == base64.b64encode(hmac.new(base64.b64decode(api_keys[api_key]['secret']),
                                              message,
                                              hashlib.sha512).digest()):
        return AuthenticationStatus.OK
    else:
        return AuthenticationStatus.INVALID_SIGNATURE
