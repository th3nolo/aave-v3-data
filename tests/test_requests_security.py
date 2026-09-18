"""Synthetic .netrc regression: no real credentials and no HTTP requests."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from requests.utils import get_netrc_auth


class RequestsCredentialTests(unittest.TestCase):
    def test_userinfo_cannot_select_another_hosts_netrc_credentials(self):
        with tempfile.TemporaryDirectory() as directory:
            netrc = Path(directory) / 'netrc'
            netrc.write_text('machine trusted.invalid login synthetic-user password synthetic-password\n', encoding='utf-8')
            with patch.dict(os.environ, {'NETRC': str(netrc)}):
                self.assertEqual(get_netrc_auth('https://trusted.invalid/path'), ('synthetic-user', 'synthetic-password'))
                self.assertIsNone(get_netrc_auth('https://trusted.invalid:443@attacker.invalid/path'))
                self.assertIsNone(get_netrc_auth('https://unrelated.invalid/path'))
