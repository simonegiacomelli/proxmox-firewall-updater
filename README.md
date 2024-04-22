# Proxmox Firewall Updater

The Proxmox Firewall Updater is a Python script designed to automate the process of updating firewall aliases based on DNS entries. This ensures that firewall configurations remain synchronized with DNS changes, enhancing security and network management in Proxmox environments.

The script only updates an alias if the IP address of the corresponding domain name changes.

The configuration of the firewall aliases to update is done by adding a comment to the alias with the domain name to resolve. 

For example, an alias with the comment `#resolve: example.com` will be updated with the IP address of `example.com`.

<img width="397" alt="image" src="https://github.com/simonegiacomelli/proxmox-firewall-updater/assets/3785783/85518007-756c-4804-b0a5-925b88330e02">


## Installation

To get the script on your Proxmox server, use the following command:

```bash
curl https://raw.githubusercontent.com/simonegiacomelli/proxmox-firewall-updater/main/update_firewall_aliases.py -o update_firewall_aliases.py
```

### Scheduling with Cron

You can add a cron job to run the script every 5 minutes. The output of the script will be logged to the system log using the `logger` command:

```bash
(crontab -l 2>/dev/null; echo "*/5 * * * * /usr/bin/env python3 $(pwd)/update_firewall_aliases.py 2>&1 | logger -t update_firewall_aliases.py") | crontab -
```

### Scheduling without Cron

If you prefer to avoid verbose cron job logs, you can create a script with a loop that runs the script every 5 minutes. To activate this script, add it to the @reboot cron job:

```bash
echo "while true; do (python3 $(pwd)/update_firewall_aliases.py | logger -t update_firewall_aliases.py); sleep 300; done" > firewall_aliases_updater_forever.sh
chmod +x firewall_aliases_updater_forever.sh
(crontab -l 2>/dev/null; echo "@reboot /bin/bash -c $(pwd)/firewall_aliases_updater_forever.sh &") | crontab -
```

## Command Line Options

The script supports two optional command line options:

- `--dry-run`: Executes the script without making any changes. This is useful for testing and debugging.
- `--verbose`: Provides detailed logging of operations, which can aid in understanding the script's behavior and troubleshooting.

You can use both options together for a detailed dry run:

```bash
python3 update_firewall_aliases.py --dry-run --verbose
```

In this mode, the script will print detailed logs of its intended actions without actually making any changes.


# Internal Workings

## Automated Tests

This project includes comprehensive automated tests to ensure its reliability and correctness. These tests cover various scenarios and edge cases, providing a robust safety net for ongoing development.

The tests are written using Python's built-in `unittest` module, and they thoroughly test the functionality of the script, including the parsing of the configuration file, DNS resolution, and the creation and updating of firewall aliases.

To run the tests, use the following command:

```bash
python3 -m unittest update_firewall_aliases_test.py
```

## Proxmox API

The script uses `pvesh` commands to get, create, and set Proxmox VE firewall aliases. For more details, refer to the Proxmox VE API documentation.

### pvesh get
Get aliases:

`pvesh get cluster/firewall/aliases --output-format json`

Example output:

```json
[{"cidr":"1.2.3.4","comment":"comment foo #resolve: example.com","digest":"48ba54e4cabe338b1cb490bb9c5b617f61bd4212","ipversion":4,"name":"alias_example_com"},{"cidr":"0.0.0.0","comment":"comment bar #resolve: example.net","digest":"48ba54e4cabe338b1cb490bb9c5b617f61bd4212","ipversion":4,"name":"alias_example_net"}]
```

### pvesh set
`pvesh set cluster/firewall/aliases/alias_example_com -cidr 1.2.3.4 -comment "comments are kept as is"`


## Relevant Proxmox Forum Thread

For more information, check out this [Proxmox Forum thread](https://forum.proxmox.com/threads/firewall-alias-with-domainname.43036/) on firewall aliases with domain names.
