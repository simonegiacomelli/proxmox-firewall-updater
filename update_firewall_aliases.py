#!/usr/bin/env python3
from __future__ import annotations

import argparse
import configparser
import json
import shlex
import socket
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List

SECTION_NAME = 'alias to domain'
DEFAULT_COMMENT = 'Generated by update_firewall_aliases.py'

ini_path = Path(__file__).parent / 'firewall_aliases.ini'


@dataclass(frozen=True)
class DomainEntry:
    domain: str
    alias: str
    ip: str = ''


@dataclass(frozen=True)
class AliasEntry:
    name: str
    cidr: str
    comment: str


class Dependencies:
    """Interface for managing actions on pve firewall aliases and dns entries."""

    def __init__(self):
        self.verbose = True
        self.dry_run = True

    def domains_list(self) -> List[DomainEntry]: ...

    def alias_get(self, name: str) -> AliasEntry | None: ...

    def alias_create(self, alias: AliasEntry): ...

    def alias_set(self, alias: AliasEntry): ...

    def dns_resolve(self, domain: str) -> str | None: ...


def domains_list(ini_path: Path) -> List[DomainEntry]:
    config = configparser.ConfigParser()
    if not ini_path.exists():
        return []
    config.read_string(ini_path.read_text())
    if SECTION_NAME not in config:
        return []
    entries = []
    for key in config[SECTION_NAME]:
        domain = config[SECTION_NAME][key]
        entries.append(DomainEntry(domain=domain, alias=key))
    return entries


def _update_domain_entry(domain_entry: DomainEntry, deps: Dependencies):
    ip = deps.dns_resolve(domain_entry.domain)
    if ip is None:
        return
    alias = deps.alias_get(domain_entry.alias)

    if alias is None:
        new_alias = AliasEntry(name=domain_entry.alias, cidr=ip, comment=DEFAULT_COMMENT)
        deps.alias_create(new_alias)
    else:
        if alias.cidr != ip:
            new_alias = AliasEntry(name=alias.name, cidr=ip, comment=alias.comment)
            deps.alias_set(new_alias)


def update_aliases(deps: Dependencies):
    domain_entries = deps.domains_list()

    if deps.verbose:
        log(f'found {len(domain_entries)} domain entries. dry-run={deps.dry_run}')
        for domain_entry in domain_entries:
            log(f'{domain_entry.alias} = {domain_entry.domain}')

    for domain_entry in domain_entries:
        _update_domain_entry(domain_entry, deps)


def log(msg):
    print(msg)


class Run:
    def __init__(self, cmd, cwd=None):
        self.cmd = cmd
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd)
        self.returncode = res.returncode
        self.success = res.returncode == 0
        self.stdout = res.stdout.decode("utf-8")
        self.stderr = res.stderr.decode("utf-8")

    def __str__(self):
        st = 'OK' if self.success else f'FAILED status={self.returncode}'
        return \
            f'status={st}\n' \
            f'command={" ".join(self.cmd)}\n' \
            f'stdout: ------------------------------\n' \
            f'{self.stdout}\n' \
            f'stderr: ------------------------------\n' \
            f'{self.stderr}'


class ProdDependencies(Dependencies):

    def __init__(self, args):
        super().__init__()
        self.verbose = args.verbose
        self.dry_run = args.dry_run

    def domains_list(self) -> List[DomainEntry]:
        return domains_list(ini_path)

    def alias_get(self, name: str) -> AliasEntry | None:
        cmd = f'pvesh get cluster/firewall/aliases/{name} --output-format json'.split(' ')
        run = self._run(cmd, skip=False)
        if not run.success:
            return None
        else:
            # {"cidr":"1.2.3.4","comment":"comment foo","ipversion":4,"name":"alias_example_com"}
            alias = json.loads(run.stdout)
            return AliasEntry(name=alias['name'], cidr=alias['cidr'], comment=alias['comment'])

    def alias_create(self, alias: AliasEntry):
        cmd = f'pvesh create cluster/firewall/aliases --cidr {alias.cidr} --name {alias.name} --comment'.split(' ')
        cmd += [alias.comment]
        self._run(cmd, skip=self.dry_run)

    def alias_set(self, alias: AliasEntry):
        cmd = f'pvesh set cluster/firewall/aliases/{alias.name} --cidr {alias.cidr} --comment'.split(' ')
        cmd += [alias.comment]
        self._run(cmd, skip=self.dry_run)

    def dns_resolve(self, domain: str) -> str | None:
        try:
            (_, _, ipaddrlist) = socket.gethostbyname_ex(domain)
            if len(ipaddrlist) > 0:
                if self.verbose:
                    log(f'{domain} resolved to {ipaddrlist[0]}')
                return ipaddrlist[0]
        except:
            return None

    def _run(self, cmd, skip: bool) -> Run | None:
        if self.verbose:
            dr = 'executing:' if self.dry_run else 'dry-run:'
            log(f'{dr} {shlex.join(cmd)}')
        if not skip:
            run = Run(cmd)
            if self.verbose:
                log(str(run))
            return run


def main():
    parser = argparse.ArgumentParser(description='Update firewall aliases.')
    parser.add_argument('--dry-run', action='store_true', help='run the script without making any changes')
    parser.add_argument('--verbose', action='store_true', help='print detailed operations information')

    args = parser.parse_args()
    update_aliases(ProdDependencies(args))


if __name__ == '__main__':
    main()
