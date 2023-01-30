#!/usr/bin/env python
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ipalib import api
import json
from distutils.version import StrictVersion


def initialize():
    '''
    This function initializes the FreeIPA/IPA API. This function requires
    no arguments. A kerberos key must be present in the users keyring in
    order for this to work.
    '''

    api.bootstrap(context='cli')
    api.finalize()
    try:
        api.Backend.rpcclient.connect()
    except AttributeError:
        # FreeIPA < 4.0 compatibility
        api.Backend.xmlclient.connect()

    return api


def list_groups(api):
    '''
    This function prints a list of all host groups. This function requires
    one argument, the FreeIPA/IPA API object.
    '''

    inventory = {}
    hostvars = {}

    ipa_version = api.Command.env()['result']['version']
    result = api.Command.hostgroup_find()['result']

    for hostgroup in result:
        # Get direct and indirect members (nested hostgroups) of hostgroup
        members = []
        if StrictVersion(ipa_version) >= StrictVersion('4.0.0'):
            hostgroup_name = hostgroup['cn'][0]
            hostgroup = api.Command.hostgroup_show(hostgroup_name)['result']

        if 'member_host' in hostgroup:
            members = [host for host in hostgroup['member_host']]
        if 'memberindirect_host' in hostgroup:
            members += (host for host in hostgroup['memberindirect_host'])
        inventory[hostgroup['cn'][0]] = {'hosts': [host for host in members]}

        for member in members:
            hostvars[member] = {}

    inventory['_meta'] = {'hostvars': hostvars}
    inv_string = json.dumps(inventory, indent=1, sort_keys=True)
    print(inv_string)

    return None


if __name__ == '__main__':
    api = initialize()
    list_groups(api)
