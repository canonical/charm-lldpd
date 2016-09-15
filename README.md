# Overview

Purpose of this charm is to install and configure LLDP daemon (lldpd). LLDP
is used by network administrators to detect how machines are connected to
switches and routers.

# Usage

Step by step instructions on using the charm:

juju deploy lldpd
juju add-relation lldpd application-on-physical-machine

Being a subordinate charm it needs to be related to an application running
on physical machine. It doesn't make much sense to install LLDP on a VM
or LXD container, because Linux bridge will terminate LLDP traffic.

## Scale out Usage

By scaling your application, subordinate charm will get installed automatically.

## Known Limitations and Issues

LLDP is not very useful on containers and virtual machines and therefore it's
use on those is not recommended.

# Configuration

By default LLDPd will listen on all interfaces and pick, more or less, a random
systemid. Two given configuration options allow user to specify which interfaces
will be used to broadcast LLDP data and which will be used for systemid.

One additional option, i40e-lldp-stop, is included because some Intel NICs
block user-space LLDP generated data and instead broadcast their own. By setting
this option to True (default), NIC's built-in LLDP daemon will be disabled, if
such a NIC has been discovered on the system.
