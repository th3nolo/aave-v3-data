"""Malformed input must produce findings, never escape the validator as a crash."""
import unittest
from validation import validate_aave_data


class ValidationBoundaryTests(unittest.TestCase):
    def test_invalid_structures_are_reported(self):
        for data in (None, [], {'ethereum': 'not-a-list'}, {'ethereum': [None]}, {'ethereum': [{}]}):
            with self.subTest(data=data):
                result = validate_aave_data(data)
                self.assertFalse(result.is_valid())
                self.assertTrue(result.errors)
