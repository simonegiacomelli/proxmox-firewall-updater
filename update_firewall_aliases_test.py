#!/usr/bin/env python3
from __future__ import annotations

import unittest
from typing import Dict, List

from update_firewall_aliases import Dependencies, AliasEntry, update_aliases


class update_domain_entry_TestCase(unittest.TestCase):

    def setUp(self) -> None:
        self.deps = DependenciesFake()

    def tearDown(self) -> None:
        pass

    def test_stale_entry__should_be_changed(self):
        # GIVEN
        self.deps.alias_set(AliasEntry(name='alias1', cidr='0.0.0.0', comment='#resolve: example.com'))
        self.deps.dns_entries['example.com'] = '1.2.3.4'

        # WHEN
        update_aliases(self.deps)

        # THEN
        expect = AliasEntry(name='alias1', cidr='1.2.3.4', comment='#resolve: example.com')
        actual = self.deps.alias_entries['alias1']
        self.assertEqual(expect, actual)

    def test_up_to_date_entry__should_be_changed_only_if_dns_changes(self):
        # GIVEN
        alias_entry = AliasEntry(name='alias1', cidr='0.0.0.0', comment='#resolve: example.com')
        self.deps.alias_set(alias_entry)
        self.deps.dns_entries['example.com'] = '0.0.0.0'

        # WHEN
        update_aliases(self.deps)

        # THEN
        self.assertIs(alias_entry, self.deps.alias_entries['alias1'])

    def test_no_dns__should_not_change_the_alias(self):
        # GIVEN
        alias_entry = AliasEntry(name='alias1', cidr='0.0.0.0', comment='#resolve: example.com')
        self.deps.alias_set(alias_entry)
        # no dns entry

        # WHEN
        update_aliases(self.deps)

        # THEN
        self.assertIs(alias_entry, self.deps.alias_entries['alias1'])

    def test_confounders(self):
        # GIVEN
        comment = 'confounder 1 #resolve: 1-800-unicorn.party confounder 2'
        self.deps.alias_set(AliasEntry(name='alias1', cidr='0.0.0.0', comment=comment))
        self.deps.dns_entries['1-800-unicorn.party'] = '1.2.3.4'

        # WHEN
        update_aliases(self.deps)

        # THEN
        expect = AliasEntry(name='alias1', cidr='1.2.3.4', comment=comment)
        actual = self.deps.alias_entries['alias1']
        self.assertEqual(expect, actual)

    def test_invalid__should_not_change_the_alias(self):
        # GIVEN
        comment = '#resolve: '
        alias_entry = AliasEntry(name='alias1', cidr='0.0.0.0', comment=comment)
        self.deps.alias_set(alias_entry)

        # WHEN
        update_aliases(self.deps)

        # THEN
        self.assertEqual(alias_entry, self.deps.alias_entries['alias1'])


class DependenciesFake(Dependencies):

    def __init__(self):
        super().__init__()
        self.alias_entries: Dict[str, AliasEntry] = {}
        self.dns_entries: Dict[str, str] = {}
        self.domains_entries = []

    def alias_list(self) -> List[AliasEntry]:
        return list(self.alias_entries.values())

    def alias_set(self, alias: AliasEntry):
        self.alias_entries[alias.name] = alias

    def dns_resolve(self, domain: str) -> str | None:
        return self.dns_entries.get(domain, None)
