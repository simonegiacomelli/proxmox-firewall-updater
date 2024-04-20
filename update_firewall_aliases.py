#!/usr/bin/env python3

import configparser
from dataclasses import dataclass, field
from typing import List

SECTION_NAME = "domain to alias"

@dataclass()
class DomainEntry:
    domain: str
    alias: str


def domain_to_alias_list(ini_content: str) -> List[DomainEntry]:
    config = configparser.ConfigParser()
    config.read_string(ini_content)
    if SECTION_NAME not in config:
        return []
    domain = []
    for key in config[SECTION_NAME]:
        domain.append(DomainEntry(domain=key, alias=config[SECTION_NAME][key]))
    return domain

def update(domain_entries: List[DomainEntry]):
    with open('firewall_aliases.ini') as f:
        ini_content = f.read()
    domain_entries = domain_to_alias_list(ini_content)
    for domain_entry in domain_entries:
        print(f'{domain_entry.domain} -> {domain_entry.alias}')