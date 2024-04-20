#!/usr/bin/env python3

import configparser
from dataclasses import dataclass, field
from typing import List


@dataclass()
class DomainEntry:
    domain: str
    alias: str


def domain_to_alias_list(ini_content: str) -> List[DomainEntry]:
    config = configparser.ConfigParser()
    config.read_string(ini_content)
    domain = []
    for section in config.sections():
        for key in config[section]:
            domain.append(DomainEntry(domain=key, alias=config[section][key]))
    return domain
