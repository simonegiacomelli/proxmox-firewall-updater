# proxmox-firewall-updater
This script facilitates automatic updates to firewall aliases based on DNS entries, enabling dynamic FQDN firewall rules in Proxmox environments. It's designed to ensure that firewall configurations remain synchronized with DNS changes, enhancing security and network management.

## Proxmox Forum Interesting thread
[Firewall Alias with Domainname](https://forum.proxmox.com/threads/firewall-alias-with-domainname.43036/)

## Commands used by this script

This script uses these commands to read/write pve firewall aliases 
`pvesh get cluster/firewall/aliases --output-format json`
`pvesh create cluster/firewall/aliases -name alias_example_com -cidr 1.2.3.4 -comment "created by proxmox-firewall-updater"`
`pvesh set cluster/firewall/aliases/alias_example_com -cidr 1.2.3.4 -comment "comments are kept as is"`

## Instructions

set the configuration in update_firewall_aliases.ini, for example:

```
[dns to alias]
example.com = alias_example_com
```