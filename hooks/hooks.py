#!/usr/bin/env python3
#
# Copyright 2016-2018 Canonical Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import os
import sys

_path = os.path.dirname(os.path.realpath(__file__))
_parent = os.path.abspath(os.path.join(_path, ".."))


def _add_path(path):
    if path not in sys.path:
        sys.path.insert(1, path)


_add_path(_parent)

from charmhelpers.core import hookenv, host  # noqa: E402
from charmhelpers import fetch  # noqa: E402

PACKAGES = ['lldpd']

hooks = hookenv.Hooks()


@hooks.hook('install')
def install():
    hookenv.status_set('maintenance', 'Installing LLDP daemon')
    fetch.apt_update()
    fetch.apt_install(PACKAGES, fatal=False)
    hookenv.status_set('maintenance', 'LLDP daemon installed')


@hooks.hook("config-changed")
def config_changed():
    hookenv.status_set('maintenance', 'Configuring LLDP daemon')
    configs = hookenv.config()
    if 'i40e-lldp-stop' in configs:
        disable_i40e_lldp()
    lldpdconf = "/etc/default/lldpd"
    conf = open(lldpdconf, 'w')
    args = ['DAEMON_ARGS=\"']
    if 'systemid-from-interface' in configs:
        args.append('-C %s ' % str(configs['systemid-from-interface']))
    if 'interfaces-regex' in configs:
        args.append('-I %s ' % str(configs['interfaces-regex']))
    if configs['enable-snmp']:
        args.append('-x ')
    if configs['short-name']:
        short_name()
    machine_id = os.environ['JUJU_MACHINE_ID']
    if machine_id:
        args.append('-S juju_machine_id=%s' % str(machine_id))
    args.append('\"\n')
    conf.write(''.join(args))
    conf.close()
    host.service_restart('lldpd')
    hookenv.status_set('active', 'LLDP daemon running')


def disable_i40e_lldp():
    path = '/sys/kernel/debug/i40e'
    if not os.path.exists(path):
        return True
    for nic in os.listdir(path):
        cmd = open('%s/%s/command' % (str(path), str(nic)), 'w')
        cmd.write('lldp stop')
        cmd.close()


def short_name():
    path = '/etc/lldpd.conf'
    shortname = os.uname()[1]
    cmd = open('%s' % (str(path)), 'w')
    cmd.write('configure system hostname %s\n' % str(shortname))
    cmd.close()


if __name__ == '__main__':
    try:
        hooks.execute(sys.argv)
    except hookenv.UnregisteredHookError:
        pass
