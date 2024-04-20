#!/usr/bin/env python3
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from typing import Dict

from update_firewall_aliases import DomainEntry, domain_to_alias_list, Dependencies, AliasEntry, \
    SECTION_NAME, DEFAULT_COMMENT, update_aliases


class DomainToAliasList_TestCase(unittest.TestCase):

    def setUp(self) -> None:
        self.ini = Path(tempfile.mkstemp(prefix='test_', suffix='.ini')[1])
        self.ini.unlink()

    def tearDown(self) -> None:
        if self.ini.exists():
            self.ini.unlink()

    def test_two_valid_entries(self):
        self.ini.write_text("\n"
                            f"[{SECTION_NAME}]\n"
                            "example.com = alias_example_com\n"
                            "foo.org = alias_foo_rog\n")

        result = domain_to_alias_list(self.ini)

        self.assertEqual(result, [
            DomainEntry(domain='example.com', alias='alias_example_com'),
            DomainEntry(domain='foo.org', alias='alias_foo_rog')
        ])

    def test_empty_ini(self):
        self.ini.write_text('')
        result = domain_to_alias_list(self.ini)
        self.assertEqual(result, [])

    def test_wrong_section_should_be_ignored(self):
        self.ini.write_text('[some section foobar]\nexample.com = alias_example_com\n')
        result = domain_to_alias_list(self.ini)
        self.assertEqual(result, [])

    def test_file_do_not_exist(self):
        result = domain_to_alias_list(self.ini)
        self.assertEqual(result, [])


class DependenciesFake(Dependencies):

    def __init__(self):
        super().__init__()
        self.alias_get_count = 0
        self.alias_entries: Dict[str, AliasEntry] = {}
        self.dns_entries: Dict[str, str] = {}
        self.domains_entries = []

    def domains_list(self) -> list[DomainEntry]:
        return self.domains_entries

    def alias_get(self, name: str) -> AliasEntry | None:
        self.alias_get_count += 1
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
        self.deps.domains_entries.append(DomainEntry(domain='example.com', alias='alias_example_com'))
        self.deps.dns_entries['example.com'] = '1.2.3.4'
        self.deps.alias_set(AliasEntry(name='alias_example_com', cidr='0.0.0.0', comment='com1'))

        # WHEN
        update_aliases(self.deps)

        # THEN
        expect = AliasEntry(name='alias_example_com', cidr='1.2.3.4', comment='com1')
        actual = self.deps.alias_get('alias_example_com')
        self.assertEqual(expect, actual)

    def test_existing_entry__should_be_changed_only_if_dns_changes(self):
        # GIVEN
        self.deps.domains_entries.append(DomainEntry(domain='example.com', alias='alias_example_com'))
        entry = AliasEntry(name='alias_example_com', cidr='1.2.3.4', comment='com1')
        self.deps.alias_set(entry)
        self.deps.dns_entries['example.com'] = '1.2.3.4'

        # WHEN
        update_aliases(self.deps)

        # THEN
        actual = self.deps.alias_get('alias_example_com')
        self.assertIs(entry, actual)

    def test_non_existing_entry__should_be_created(self):
        # GIVEN
        self.deps.dns_entries['example.com'] = '5.6.7.8'
        self.deps.domains_entries.append(DomainEntry(domain='example.com', alias='alias_example_com'))

        # WHEN
        update_aliases(self.deps)

        # THEN
        expect = AliasEntry(name='alias_example_com', cidr='5.6.7.8', comment=DEFAULT_COMMENT)
        actual = self.deps.alias_get('alias_example_com')
        self.assertEqual(expect, actual)

    def test_no_dns__should_not_create_the_alias(self):
        # GIVEN
        self.deps.domains_entries.append(DomainEntry(domain='example.com', alias='alias_example_com'))
        # no dns entry

        # WHEN
        update_aliases(self.deps)

        # THEN
        self.assertEqual(0, self.deps.alias_get_count)
        self.assertIsNone(self.deps.alias_get('alias_example_com'))
