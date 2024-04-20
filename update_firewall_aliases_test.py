#!/usr/bin/env python3
from __future__ import annotations

import unittest
from pathlib import Path
from typing import Dict

from update_firewall_aliases import DomainEntry, domain_to_alias_list, update_domain_entry, Dependencies, AliasEntry, \
    SECTION_NAME, DEFAULT_COMMENT


class DomainToAliasList_TestCase(unittest.TestCase):

    def test_two_valid_entries(self):
        ini_content = ("\n"
                       f"[{SECTION_NAME}]\n"
                       "example.com = alias_example_com\n"
                       "foo.org = alias_foo_rog\n")
        result = domain_to_alias_list(ini_content)

        self.assertEqual(result, [
            DomainEntry(domain='example.com', alias='alias_example_com'),
            DomainEntry(domain='foo.org', alias='alias_foo_rog')
        ])

    def test_empty_ini(self):
        ini_content = ""
        result = domain_to_alias_list(ini_content)
        self.assertEqual(result, [])

    def test_wrong_section_should_be_ignored(self):
        ini_content = "[some section foobar]\nexample.com = alias_example_com\n"
        result = domain_to_alias_list(ini_content)
        self.assertEqual(result, [])


class DependenciesFake(Dependencies):

    def __init__(self):
        self.alias_entries: Dict[str, AliasEntry] = {}
        self.dns_entries: Dict[str, str] = {}

    def alias_get(self, name: str) -> AliasEntry | None:
        return self.alias_entries.get(name, None)

    def alias_create(self, alias: AliasEntry):
        self.alias_entries[alias.name] = alias

    def alias_set(self, alias: AliasEntry):
        self.alias_entries[alias.name] = alias

    def dns_resolve(self, domain: str) -> str | None:
        return self.dns_entries.get(domain, None)


class update_domain_entry_TestCase(unittest.TestCase):

    def setUp(self) -> None:
        self.deps = DependenciesFake()

    def tearDown(self) -> None:
        pass

    def test_existing_entry__should_be_changed(self):
        # GIVEN
        self.deps.alias_set(AliasEntry(name='alias_example_com', cidr='0.0.0.0', comment='com1'))
        self.deps.dns_entries['example.com'] = '1.2.3.4'

        # WHEN
        update_domain_entry(DomainEntry(domain='example.com', alias='alias_example_com'), self.deps)

        # THEN
        expect = AliasEntry(name='alias_example_com', cidr='1.2.3.4', comment='com1')
        actual = self.deps.alias_get('alias_example_com')
        self.assertEqual(expect, actual)

    def test_non_existing_entry__should_be_created(self):
        # GIVEN
        self.deps.dns_entries['example.com'] = '5.6.7.8'

        # WHEN
        update_domain_entry(DomainEntry(domain='example.com', alias='alias_example_com'), self.deps)

        # THEN
        expect = AliasEntry(name='alias_example_com', cidr='5.6.7.8', comment=DEFAULT_COMMENT)
        actual = self.deps.alias_get('alias_example_com')
        self.assertEqual(expect, actual)
