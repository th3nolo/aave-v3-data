"""The gate must fail even when application code swallows a network error."""
from pathlib import Path
import subprocess
import sys
import unittest


class OfflineGateTests(unittest.TestCase):
    def run_gate(self, body):
        code = (
            'import unittest, socket\nimport run_offline_tests\n'
            'class Probe(unittest.TestCase):\n'
            ' def test_probe(self):\n' + ''.join('  ' + line + '\n' for line in body.splitlines()) +
            'unittest.defaultTestLoader.discover = lambda *a, **k: unittest.defaultTestLoader.loadTestsFromTestCase(Probe)\n'
            'raise SystemExit(run_offline_tests.main())\n'
        )
        return subprocess.run([sys.executable, '-c', code], cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True, timeout=15)

    def test_pass_is_success(self):
        result = self.run_gate('self.assertEqual(2 + 2, 4)')
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_failure_is_not_hidden(self):
        result = self.run_gate('self.assertEqual(2 + 2, 5)')
        self.assertEqual(result.returncode, 1, result.stderr)

    def test_skip_is_not_green(self):
        result = self.run_gate("self.skipTest('synthetic skip')")
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn('does not permit skipped', result.stderr)

    def test_swallowed_external_network_is_not_green(self):
        result = self.run_gate("try:\n socket.getaddrinfo('external.invalid', 443)\nexcept RuntimeError:\n pass")
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn('external network was attempted', result.stderr)
