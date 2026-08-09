# Overview

Purpose of this charm is to install and configure LLDP daemon (lldpd). LLDP
is used by network administrators to detect how machines are connected to
switches and routers.

# Usage

Start by installing the lldpd charm and relating it to another application, e.g.

juju deploy ubuntu
juju deploy lldpd

juju integrate lldpd ubuntu

Being a subordinate charm it needs to be related to an application running
on physical machine, in the above case the Ubuntu charm.

## Scale out Usage

By scaling your application, subordinate charm will get installed automatically.

## Known Limitations and Issues

Deploying LLDP to an LXD container or virtual machine may not work as expected
due to network bridges for virtual infrastructure not passing through LLDP frames.

# Configuration

By default, LLDPd will listen on all interfaces. The interfaces-regex option
selects which interfaces LLDPd listens on and sends discovery frames from.
The systemid-from-interface option selects which interfaces LLDPd considers
when computing the chassis ID.

One additional option, i40e-lldp-stop, is included because some Intel NICs
block user-space LLDP generated data and instead broadcast their own. By setting
this option to True (default), NIC's built-in LLDP daemon will be disabled, if
such a NIC has been discovered on the system.

CDP, SONMP, and EDP support is disabled by default. The cdp-mode option provides
automatic peer-driven operation, modes that force CDPv1 or CDPv2, and
peer-driven or forced CDPv2-only operation. The sonmp-mode and edp-mode options
can enable or force their respective protocols.
