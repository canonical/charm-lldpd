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

The configuration options will be listed on the charm store, however If you're
making assumptions or opinionated decisions in the charm (like setting a default
administrator password), you should detail that here so the user knows how to
change it immediately, etc.

# Contact Information

Though this will be listed in the charm store itself don't assume a user will
know that, so include that information here:

## Upstream Project Name

  - Upstream website
  - Upstream bug tracker
  - Upstream mailing list or contact information
  - Feel free to add things if it's useful for users


[service]: http://example.com
[icon guidelines]: https://jujucharms.com/docs/stable/authors-charm-icon
