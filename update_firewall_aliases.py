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

VERSION_STRING = f'{Path(__file__).name} version 2.0.5'


@dataclass(frozen=True)
class AliasEntry:
    name: str
    cidr: str
    comment: str

    def domain(self) -> str | None:
        try:
            res = self.comment.split('#resolve: ')[1].split(' ')[0]
            if len(res) > 0:
                return res
        except:
            return None


class Dependencies:
    """Interface for managing actions on pve firewall aliases and dns entries."""

    def __init__(self):
        self.verbose = True
        self.dry_run = True

    def alias_list(self) -> List[AliasEntry]: ...

    def alias_set(self, alias: AliasEntry): ...

    def dns_resolve(self, domain: str) -> str | None: ...


def update_aliases(deps: Dependencies):
    if deps.verbose:
        log(VERSION_STRING)

    aliases = [entry for entry in deps.alias_list() if entry.domain() is not None]

    if deps.verbose:
        log(f'found {len(aliases)} aliases to check. dry-run={deps.dry_run}')
        for alias_entry in aliases:
            log(f'  {alias_entry.name} {alias_entry.domain()} cidr={alias_entry.cidr} {alias_entry.comment}')

    for alias_entry in aliases:
        ipaddr = deps.dns_resolve(alias_entry.domain())
        if ipaddr:
            if ipaddr != alias_entry.cidr:
                log(f'updating alias {alias_entry.name} from {alias_entry.cidr} to {ipaddr}')
                if not deps.dry_run:
                    deps.alias_set(AliasEntry(name=alias_entry.name, cidr=ipaddr, comment=alias_entry.comment))
            else:
                if deps.verbose:
                    log(f'alias {alias_entry.name} is up to date with {ipaddr}')
        else:
            if deps.verbose:
                log(f'cannot resolve domain `{alias_entry.domain()}` for alias `{alias_entry.name}`')


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
            f'command={shlex.join(self.cmd)}\n' \
            f'status={st}\n' \
            f'stdout: ------------------------------\n' \
            f'{self.stdout}\n' \
            f'stderr: ------------------------------\n' \
            f'{self.stderr}' \
            f'end ----------------------------------\n'


def alias_list_to_typed(alias_list: str) -> List[AliasEntry]:
    j = json.loads(alias_list)
    return [AliasEntry(name=alias['name'], cidr=alias['cidr'], comment=alias['comment']) for alias in j]


class ProdDependencies(Dependencies):

    def __init__(self, args):
        super().__init__()
        self.verbose = args.verbose
        self.dry_run = args.dry_run

    def alias_list(self) -> List[AliasEntry]:
        cmd = f'pvesh get cluster/firewall/aliases/ --output-format json'.split(' ')
        run = self._run(cmd, skip=False)
        if not run.success:
            return []
        else:
            return alias_list_to_typed(run.stdout)

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
        if self.verbose and skip:
            log(f'dry-run: {shlex.join(cmd)}')
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
