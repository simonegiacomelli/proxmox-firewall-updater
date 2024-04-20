# proxmox-firewall-updater
This script facilitates automatic updates to firewall aliases based on DNS entries, enabling dynamic FQDN firewall rules in Proxmox environments. It's designed to ensure that firewall configurations remain synchronized with DNS changes, enhancing security and network management.

The alias will only be updated if the IP address of the corresponding domain name changes.

Please note that this script is designed to create and update firewall aliases based on the configuration file, but it does not delete any existing entries. 
If an entry in the firewall aliases is no longer needed or if it's not present in the configuration file, 
the script will not automatically remove it. 



# Installation

Get the script to your Proxmox server and add a cron job to run it periodically.

```
curl -o update_firewall_aliases.py https://raw.githubusercontent.com/simonegiacomelli/proxmox-firewall-updater/main/update_firewall_aliases.py
```



The following command will add a cron job to run the script every 5 minutes:

```
(crontab -l 2>/dev/null; echo "*/5 * * * * /bin/sh /root/update_firewall_aliases.py") | crontab -
```


# Configuration

The default configuration file is named `update_firewall_aliases.ini` and it is searched in the same folder as the script.

The configuration file is in INI format and contains a list of DNS names and their corresponding firewall aliases.
The script will create or update the firewall aliases based on the configuration file.
The description of the alias will be reused, if the alias already exists.

Example of a configuration file:

```
[alias to domain]
alias_example_com = example.com 
```

[//]: # (You can specify the full path of the configuration file using `-ini` option.)

[//]: # (`update_firewall_aliases.py -ini /root/my_custom_config.ini`)


## Proxmox Forum Interesting thread
[Firewall Alias with Domainname](https://forum.proxmox.com/threads/firewall-alias-with-domainname.43036/)

# Documentation of internal workings

This script uses `pvesh` commands to get/create/set pve firewall aliases.
See below for more details.

## pvesh get
Get a single alias by name:

`pvesh get cluster/firewall/aliases/alias_example_com --output-format json`

Example output:

```json
{"cidr":"1.2.3.4","comment":"dynamic ip for example.com","ipversion":4,"name":"alias_example_com"}
```

## pvesh create
`pvesh create cluster/firewall/aliases -name alias_example_com -cidr 1.2.3.4 -comment "created by proxmox-firewall-updater"`
- If it succeeds, it will return empty output and 0 exit code.
- If it fails, it will return error message and non-zero exit code.
Example output:
```
400 Parameter verification failed.
name: alias 'alias_example_com' already exists
... (truncated for brevity)
```

## pvesh set
`pvesh set cluster/firewall/aliases/alias_example_com -cidr 1.2.3.4 -comment "comments are kept as is"`


# Proxmox Forum Interesting thread
[Firewall Alias with Domainname](https://forum.proxmox.com/threads/firewall-alias-with-domainname.43036/)
