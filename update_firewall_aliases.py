#!/usr/bin/env python3
# for more information see https://github.com/simonegiacomelli/proxmox-firewall-updater

from __future__ import annotations

import argparse
import json
import shlex
import socket
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List

VERSION_STRING = f'{Path(__file__).name} version 2.0.0'


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

    def alias_list(self) -> List[AliasEntry]: ...

    def alias_set(self, alias: AliasEntry): ...

    def dns_resolve(self, domain: str) -> str | None: ...


def update_aliases(deps: Dependencies):
    alias_list = deps.alias_list()
    for alias_entry in alias_list:
        if '#resolve: ' in alias_entry.comment:
            domain = alias_entry.comment.split('#resolve: ')[1].split(' ')[0]
            ipaddr = deps.dns_resolve(domain)
            if ipaddr and ipaddr != alias_entry.cidr:
                deps.alias_set(AliasEntry(name=alias_entry.name, cidr=ipaddr, comment=alias_entry.comment))
            else:
                pass
                # log(f'cannot resolve domain `{domain}` for alias `{alias_entry.name}`')

    pass
    # domain_entries = deps.domains_list()
    #
    # if deps.verbose:
    #     log(VERSION_STRING)
    #     log(f'found {len(domain_entries)} domain entries. dry-run={deps.dry_run}')
    #     for domain_entry in domain_entries:
    #         log(f'{domain_entry.alias} = {domain_entry.domain}')
    #
    # for domain_entry in domain_entries:
    #     _update_domain_entry(domain_entry, deps)


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

    def alias_list(self) -> List[AliasEntry]:
        cmd = f'pvesh get cluster/firewall/aliases/{name} --output-format json'.split(' ')
        run = self._run(cmd, skip=False)
        if not run.success:
            return None
        else:
            # {"cidr":"1.2.3.4","comment":"comment foo","ipversion":4,"name":"alias_example_com"}
            alias = json.loads(run.stdout)
            return AliasEntry(name=alias['name'], cidr=alias['cidr'], comment=alias['comment'])

    def alias_set(self, alias: AliasEntry):
        cmd = f'pvesh set cluster/firewall/aliases/{alias.name} --cidr {alias.cidr} --comment'.split(' ')
        cmd += [alias.comment]
        self._run(cmd, skip=self.dry_run)

    def dns_resolve(self, domain: str) -> str | None:
        try:
            (_, _, ipaddrlist) = socket.gethostbyname_ex(domain)
            if self.verbose:
                log(f'{domain} resolved to `{ipaddrlist}`; using the first if present')
            if len(ipaddrlist) > 0:
                return ipaddrlist[0]
        except:
            return None

    def _run(self, cmd, skip: bool) -> Run | None:
        if self.verbose:
            dr = 'dry-run:' if self.dry_run else 'executing:'
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
