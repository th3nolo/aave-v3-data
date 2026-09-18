"""Discover every tests/test_*.py case; deny external networking, allow loopback."""
import os
from pathlib import Path
import sys
import tempfile
import unittest


def main():
    root = Path(__file__).resolve().parent
    os.chdir(root)
    sys.path.insert(0, str(root))
    sys.path.insert(0, str(root / 'src'))
    guard = root / 'tests' / 'network_guard'
    sys.path.insert(0, str(guard))
    with tempfile.TemporaryDirectory(prefix='aave-offline-') as directory:
        violations = Path(directory) / 'network-violations.txt'
        os.environ['AAVE_NETWORK_VIOLATIONS'] = str(violations)
        os.environ['PYTHONPATH'] = str(guard) + os.pathsep + os.environ.get('PYTHONPATH', '')
        # Parent interpreter is already started; workers load this automatically.
        import sitecustomize
        suite = unittest.defaultTestLoader.discover('tests', top_level_dir='.')
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        blocked = violations.exists() and violations.stat().st_size > 0
        if blocked:
            print('FAIL: external network was attempted, even if a test swallowed the error.', file=sys.stderr)
        if result.skipped or result.expectedFailures:
            print('FAIL: offline gate does not permit skipped or expected-failure tests.', file=sys.stderr)
        return int(not result.wasSuccessful() or blocked or bool(result.skipped) or bool(result.expectedFailures) or result.testsRun == 0)


if __name__ == '__main__':
    sys.exit(main())
