# proxmox-firewall-updater
This script facilitates automatic updates to firewall aliases based on DNS entries, enabling dynamic FQDN firewall rules in Proxmox environments. It's designed to ensure that firewall configurations remain synchronized with DNS changes, enhancing security and network management.

The alias will only be updated if the IP address of the corresponding domain name changes.

Please note that this script is designed to create and update firewall aliases based on the configuration file, but it does not delete any existing entries. 
If an entry in the firewall aliases is no longer needed or if it's not present in the configuration file, 
the script will not automatically remove it. 

## Command Line Options

This script supports two command line options: `--dry-run` and `--verbose`, both optional.

- `--dry-run`: Runs the script without making any changes, useful for testing and debugging.
- `--verbose`: Provides detailed logging of operations, aiding in understanding the script's behavior and troubleshooting.

You can use both options together for a detailed dry run:

```bash
python3 update_firewall_aliases.py --dry-run --verbose
```

In this mode, the script will print detailed logs of what it would do, without actually making any changes.


# Installation

Get the script to your Proxmox server in your favorite folder.

```
curl https://raw.githubusercontent.com/simonegiacomelli/proxmox-firewall-updater/main/update_firewall_aliases.py -o update_firewall_aliases.py
```

## Cron

The following command will add a cron job to run the script every 5 minutes. 
It will also log the output of the script to the system log using the `logger` command.

```
(crontab -l 2>/dev/null; echo "*/5 * * * * /usr/bin/env python3 $(pwd)/update_firewall_aliases.py 2>&1 | logger -t update_firewall_aliases.py") | crontab -
```

## Without Cron

To avoid the annoying cron jon logs, you can create a script with a loop that runs the script every 5 minutes.
To activate this script, you can add it to the @reboot cron job.

```
echo "while true; do (python3 $(pwd)/update_firewall_aliases.py | logger -t update_firewall_aliases.py); sleep 300; done" > run_firewall_aliases_updater.sh
(crontab -l 2>/dev/null; echo "@reboot /usr/bin/env python3 $(pwd)/update_firewall_aliases.sh") | crontab -
```

# Configuration

The default configuration file is named `firewall_aliases.ini` and it is searched in the same folder as the script.

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
