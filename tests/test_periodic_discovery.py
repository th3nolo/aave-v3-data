"""Offline regression coverage for periodic discovery admission and fallback."""

from contextlib import redirect_stdout
from copy import deepcopy
from io import StringIO
import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import networks


class TestPeriodicDiscovery(unittest.TestCase):
    def setUp(self):
        self.original = deepcopy(networks.AAVE_V3_NETWORKS)
        self.valid = deepcopy(self.original['ethereum'])

    def discover(self, candidates, errors=(), rpc=(True, 'accessible')):
        output = StringIO()
        with patch.object(networks, 'update_networks_from_address_book',
                          return_value=(candidates, list(errors))), \
                patch.object(networks, 'test_rpc_connectivity',
                             return_value=rpc) as probe, redirect_stdout(output):
            result, success = networks.periodic_network_discovery()
        self.assertEqual(networks.AAVE_V3_NETWORKS, self.original)
        return result, success, probe, output.getvalue()

    def test_invalid_candidate_is_absent_and_reports_failure(self):
        result, success, probe, output = self.discover(
            {**self.original, 'invalid': {'name': 'Incomplete'}})
        self.assertNotIn('invalid', result)
        self.assertEqual(result, self.original)
        self.assertFalse(success)
        probe.assert_not_called()
        self.assertIn('invalid', output)
        self.assertIn('Missing required field', output)

    def test_unreachable_candidate_is_absent_and_reports_failure(self):
        result, success, probe, output = self.discover(
            {**self.original, 'unreachable': self.valid},
            rpc=(False, 'synthetic timeout'))
        self.assertNotIn('unreachable', result)
        self.assertEqual(result, self.original)
        self.assertFalse(success)
        probe.assert_called_once_with('unreachable', self.valid)
        self.assertIn('synthetic timeout', output)

    def test_valid_candidate_is_included(self):
        result, success, probe, _ = self.discover({'accepted': self.valid})
        self.assertEqual(result, {**self.original, 'accepted': self.valid})
        self.assertTrue(success)
        probe.assert_called_once_with('accepted', self.valid)

    def test_partial_rejection_preserves_accepted_candidate(self):
        result, success, probe, _ = self.discover(
            {**self.original, 'accepted': self.valid, 'invalid': {}})
        self.assertEqual(result, {**self.original, 'accepted': self.valid})
        self.assertFalse(success)
        probe.assert_called_once_with('accepted', self.valid)

    def test_existing_updates_are_preserved_without_new_rpc_requirement(self):
        updated = {**self.valid, 'name': 'Updated Ethereum'}
        result, success, probe, _ = self.discover({'ethereum': updated})
        self.assertEqual(result, {**self.original, 'ethereum': updated})
        self.assertTrue(success)
        probe.assert_not_called()

    def test_no_changes_is_successful(self):
        result, success, probe, _ = self.discover(self.original)
        self.assertEqual(result, self.original)
        self.assertTrue(success)
        probe.assert_not_called()

    def test_upstream_errors_discard_batch_and_report_reason(self):
        result, success, probe, output = self.discover(
            {'ethereum': {**self.valid, 'name': 'Update'}, 'new': self.valid},
            errors=['synthetic address-book failure'])
        self.assertEqual(result, self.original)
        self.assertFalse(success)
        probe.assert_not_called()
        self.assertIn('synthetic address-book failure', output)

    def test_update_exception_preserves_originals(self):
        with patch.object(networks, 'update_networks_from_address_book',
                          side_effect=RuntimeError('synthetic update failure')), \
                redirect_stdout(StringIO()) as output:
            result, success = networks.periodic_network_discovery()
        self.assertEqual(result, self.original)
        self.assertFalse(success)
        self.assertIn('synthetic update failure', output.getvalue())

    def test_candidate_exception_does_not_discard_other_candidates(self):
        def probe(key, config):
            if key == 'a_broken':
                raise RuntimeError('synthetic probe failure')
            return True, 'accessible'

        with patch.object(networks, 'update_networks_from_address_book',
                          return_value=({'a_broken': self.valid,
                                         'z_accepted': self.valid}, [])), \
                patch.object(networks, 'test_rpc_connectivity', side_effect=probe), \
                redirect_stdout(StringIO()) as output:
            result, success = networks.periodic_network_discovery()
        self.assertEqual(result, {**self.original, 'z_accepted': self.valid})
        self.assertFalse(success)
        self.assertIn('a_broken', output.getvalue())
        self.assertIn('synthetic probe failure', output.getvalue())

    def test_real_update_failure_does_not_mutate_static_fallback(self):
        # Missing non-static entries are marked deprecated by the updater.
        existing = {'ethereum': {**self.valid, 'source': 'aave-address-book'}}
        snapshot = deepcopy(existing)
        with patch.object(networks, 'AAVE_V3_NETWORKS', existing), \
                patch.object(networks, 'fetch_address_book_networks',
                             return_value={'invalid': {'name': 'Incomplete'}}), \
                redirect_stdout(StringIO()):
            result, success = networks.periodic_network_discovery()
        self.assertEqual(existing, snapshot)
        self.assertEqual(result, snapshot)
        self.assertFalse(success)


if __name__ == '__main__':
    unittest.main()
