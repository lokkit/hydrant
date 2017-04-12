# -*- coding: utf-8 -*-

import os
import sys
import logging
import logging.handlers
import json
import subprocess
from collections import OrderedDict
from time import sleep
import yaml
from ethjsonrpc import EthJsonRpc
from ethjsonrpc.exceptions import ConnectionError
from ethjsonrpc.exceptions import BadResponseError

# Setup logger
logger = logging.getLogger('lokkitLogger')
logger.setLevel(logging.INFO)
if (os.name == 'posix'):
	logger.addHandler(logging.handlers.SysLogHandler(address = '/dev/log'))
logger.addHandler(logging.StreamHandler()) # log to console

def _print_help():
    print """
Usage: lokkit-hydrant.py <configfile>

If you don't specify the <configfile> it will try to read /etc/lokkit/hydrant.yml

Example config.yml:
hydrant:
    node_ip: 127.0.0.1
    node_rpc_port: 8545
    source_account_address: 0xf16801293f34fc16470729f4ac91185595aa6e10
    source_account_password: lokkit
    wei_per_request: 1000000000000000000
"""


def _check_if_exists(yaml_doc, attribute):
    """
    Checks if attribute exists in yaml_doc and log, if it does
    not exist

    Args:
        yaml_doc: The doc received by yaml.load()
        attribute: The attribute as string

    Returns:
        True if successful
    """
    if not yaml_doc.has_key(attribute):
        logger.error('Error in config file: missing key "{}"'.format(attribute))
        return False
    if yaml_doc[attribute] is None:
        logger.error('Error in config file: missing value for key "{}"'.format(attribute))
        return False
    return True

def _parse_config_file(config_filepath):
    """
    Parses the given config file and returns dict holding
    the configuration

    Args:
        config_filepath: The file path of the configuration yml

    Returns:
        A dict holding the configuration or None if an error
        occured.
    """
    doc = None
    with open(config_filepath, "r") as config_file:
        doc = yaml.load(config_file)

    if not _check_if_exists(doc, 'hydrant'):
        return None

    doc = doc.get('hydrant')

    ret = True
    ret = ret and _check_if_exists(doc, 'node_ip')
    ret = ret and _check_if_exists(doc, 'node_rpc_port')
    ret = ret and _check_if_exists(doc, 'symmetric_key_password')
    ret = ret and _check_if_exists(doc, 'source_account_address')
    ret = ret and _check_if_exists(doc, 'source_account_password')
    ret = ret and _check_if_exists(doc, 'wei_per_request')

    if ret:
        return doc
    else:
        return None

def main():
    """
    Runs hydrant and listens for incoming whispers on the configured node.
    When receiving a valid command, starts the configured script with the
    arguments address and command.
    """
    if len(sys.argv) < 2:
        config_filepath = "/etc/lokkit/hydrant.yml"
    else:
        config_filepath = sys.argv[1]

    if not os.path.isfile(config_filepath):
        logger.error('Error reading the config file "{}": The file does not exist'
                     .format(config_filepath))
        _print_help()
        return 1

    logger.info("Reading config file: {}".format(config_filepath))
    config = _parse_config_file(config_filepath)
    if not config:
        logger.error("Config file could not be parsed: {}".format(config_filepath))
        _print_help()
        return 1

    host = config['node_ip']
    port = config['node_rpc_port']
    source_account_address = config['source_account_address']
    source_account_password = config['source_account_password']
    wei_per_request = config['wei_per_request']
    symmetric_key_password = config['symmetric_key_password']

    logger.info('Connecting to {0}:{1}'.format(host, port))
    c = EthJsonRpc(host, port)

    try:
        logger.info('Node shh version: {0}'.format(c.shh_version()))
    except ConnectionError:
        logger.error('Could not connect to {0}:{1}'.format(host, port))
        return
    except:
        logger.error('Shh is not enabled on this node.')
        return

    # config
    topics = []
    try:
        balance = c.eth_getBalance(source_account_address)
        c.personal_unlockAccount(source_account_address, source_account_password)

        hydrant_sha3 = c.web3_sha3("hydrant")
        topics.append(hydrant_sha3[:8])
        logger.info('Configured hydrant\n\
    source_account_address: {0}\n\
    available balance at start: {1} wei\n\
    wei_per_request: {2}'.format(source_account_address, balance, wei_per_request))

    except BadResponseError as e:
        logger.error('something went wrong while unlocking the account: {0}'.format(e))
        return

    symmetric_key_address = c.shh_addSymmetricKeyFromPassword(symmetric_key_password)

    filter_id = c.shh_subscribe(type='sym', key=symmetric_key_address, sig=None, minPow=None, topics=topics)
    logger.info('Listen for incomming hydrant messages..')
    try:
        while True:
            messages = c.shh_getNewSubscriptionMessages(filter_id)
            for message in messages:
                logger.debug('Message details:\n  hash {0}\n  ttl {1}\n  payload: {2}\n  topic: {3}'
                        .format(message['hash'], message['ttl'], message['payload'], message['topic']))

                payload = None
                try:
                    # payload contains digest and message
                    payload = message['payload'][2:].decode('hex')
                except:
                    logger.error('Error parsing whisper message payload: {0}'.format(message['payload']))
                    continue

                destination_address = payload
                if c.isAddress(destination_address):
                    curent_balance = c.eth_getBalance(source_account_address)
                    if curent_balance >= wei_per_request:
                        c.personal_unlockAccount(source_account_address, source_account_password)
                        tx = c.eth_sendTransaction(from_address=source_account_address, to_address=payload, value=wei_per_request)
                        logger.info('sent transaction from {0} to {1} for {2} wei. TX: {3}'.format(payload, source_account_address, wei_per_request, tx))
                    else:
                        logger.error('Not enough ETH available. Available: {0} Required: {1}'.format(curent_balance, wei_per_request))
                else:
                    logger.warn('received "{0}" which is not a valid address'.format(destination_address))

            sleep(1)
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()

