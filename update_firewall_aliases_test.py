#!/usr/bin/env python3

import unittest
from pathlib import Path

from update_firewall_aliases import DomainEntry, domain_to_alias_list


class FunctionsTestCase(unittest.TestCase):

    def test_domain_to_alias_list(self):
        ini_content = ("\n"
                       "[domain to alias]\n"
                       "example.com = alias_example_com\n"
                       "foo.org = alias_foo_rog\n")
        result = domain_to_alias_list(ini_content)

        self.assertEqual(result, [
            DomainEntry(domain='example.com', alias='alias_example_com'),
            DomainEntry(domain='foo.org', alias='alias_foo_rog')
        ])

    def test_domain_to_alias_list_empty(self):
        ini_content = ""
        result = domain_to_alias_list(ini_content)
        self.assertEqual(result, [])
