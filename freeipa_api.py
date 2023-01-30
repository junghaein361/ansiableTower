#!/usr/bin/env python

import json
import os
import requests

SERVER = os.getenv('FREEIPA_SERVER')
CA = os.getenv('FREEIPA_CA_PATH')


def authenticate():
    headers = {
        'Accept': 'text/plain',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Referer': 'https://{0}/ipa'.format(SERVER)
    }
    session = requests.Session()
    session.headers.update(headers)
    url = 'https://{0}/ipa/session/login_password'.format(SERVER)

    username = os.getenv('FREEIPA_API_USERNAME')
    password = os.getenv('FREEIPA_API_PASSWORD')

    data = 'user={0}&password={1}'.format(username, password)
    response = session.post(url, data=data, verify=CA)
    response.raise_for_status()
    session.headers.update({'Content-Type': 'application/json'})
    return session


def cmd(session, method, params=None):
    url = 'https://{0}/ipa/session/json'.format(SERVER)
    data = {
        'method': method,
        'params': [[], {}] if params is None else params
    }
    response = session.post(url, data=json.dumps(data), verify=CA)
    result = response.json()
    if 'error' in result and result['error'] is not None:
        raise Exception(result['error'])
    return result['result']['result']


def create_inventory(session):
    inventory = {}
    hostvars = {}

    result = cmd(session, 'hostgroup_find')

    for group in result:
        members = []

        group_name = group['cn'][0]
        hosts = cmd(session, 'hostgroup_show', [[group_name], {}])

        if 'member_host' in hosts:
            members = [host for host in hosts['member_host']]
        if 'memberindirect_host' in hosts:
            members += (host for host in hosts['memberindirect_host'])

        inventory[group_name] = {'hosts': [host for host in members]}

        for member in members:
            hostvars[member] = {}

    inventory['_meta'] = {'hostvars': hostvars}
    return inventory


def main():

    session = authenticate()
    try:
        inventory = create_inventory(session)
    finally:
        cmd(session, 'session_logout')

    inv_string = json.dumps(inventory, indent=1, sort_keys=True)
    print(inv_string)


if __name__ == '__main__':
    main()
