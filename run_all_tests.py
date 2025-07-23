#!/usr/bin/env python3
"""
Run All Tests Script
Executes all local testing and validation scripts in sequence.
"""

import sys
import os
import subprocess
import time
import argparse
from typing import List, Tuple
from datetime import datetime


class TestSuiteRunner:
    """Runner for all test suites."""
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.results = []
        self.start_time = time.time()
    
    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp."""
        if self.verbose:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] {level}: {message}")
    
    def run_script(self, script_name: str, args: List[str] = None) -> Tuple[bool, str]:
        """Run a Python script and return success status and output."""
        if args is None:
            args = []
        
        cmd = [sys.executable, script_name] + args
        self.log(f"🚀 Running: {' '.join(cmd)}")
        
        start_time = time.time()
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )
            
            duration = time.time() - start_time
            success = result.returncode == 0
            
            if success:
                self.log(f"✅ {script_name} completed successfully ({duration:.1f}s)")
            else:
                self.log(f"❌ {script_name} failed with exit code {result.returncode} ({duration:.1f}s)")
                if self.verbose and result.stderr:
                    self.log(f"Error output: {result.stderr[:500]}...")
            
            self.results.append({
                "script": script_name,
                "success": success,
                "duration": duration,
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            })
            
            return success, result.stdout
            
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            self.log(f"⏰ {script_name} timed out after {duration:.1f}s")
            self.results.append({
                "script": script_name,
                "success": False,
                "duration": duration,
                "exit_code": -1,
                "stdout": "",
                "stderr": "Timeout"
            })
            return False, "Timeout"
            
        except Exception as e:
            duration = time.time() - start_time
            self.log(f"🔴 {script_name} failed with exception: {e}")
            self.results.append({
                "script": script_name,
                "success": False,
                "duration": duration,
                "exit_code": -1,
                "stdout": "",
                "stderr": str(e)
            })
            return False, str(e)
    
    def print_summary(self):
        """Print execution summary."""
        total_time = time.time() - self.start_time
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r["success"])
        failed_tests = total_tests - passed_tests
        
        print("\n" + "="*80)
        print("COMPLETE TEST SUITE SUMMARY")
        print("="*80)
        print(f"⏱️  Total execution time: {total_time:.1f}s")
        print(f"🧪 Test scripts run: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📈 Success rate: {passed_tests/max(total_tests, 1)*100:.1f}%")
        
        print(f"\n📋 Individual Script Results:")
        for result in self.results:
            status_emoji = "✅" if result["success"] else "❌"
            print(f"  {status_emoji} {result['script']:30} {result['duration']:6.1f}s (exit: {result['exit_code']})")
        
        if failed_tests > 0:
            print(f"\n❌ Failed Scripts Details:")
            for result in self.results:
                if not result["success"]:
                    print(f"  🔴 {result['script']}:")
                    if result["stderr"]:
                        print(f"     Error: {result['stderr'][:200]}...")
        
        print("="*80)
        
        return passed_tests == total_tests


def check_prerequisites() -> bool:
    """Check if all required files exist."""
    required_files = [
        'test_runner.py',
        'validate_protocol_parameters.py',
        'validate_2025_parameters.py',
        'test_workflow_integration.py',
        'aave_fetcher.py'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing required files: {missing_files}")
        return False
    
    return True


def main():
    """Main test suite runner."""
    parser = argparse.ArgumentParser(description='Run All Aave V3 Tests')
    parser.add_argument('--quick', action='store_true', help='Run quick tests only (skip data fetching)')
    parser.add_argument('--validation-only', action='store_true', help='Run validation tests only')
    parser.add_argument('--integration-only', action='store_true', help='Run integration tests only')
    parser.add_argument('--fetch-data', action='store_true', help='Fetch fresh data before validation')
    parser.add_argument('--save-reports', action='store_true', help='Save all test reports')
    parser.add_argument('--verbose', action='store_true', default=True, help='Verbose output')
    
    args = parser.parse_args()
    
    print("🧪 Aave V3 Complete Test Suite Runner")
    print("=" * 50)
    
    # Check prerequisites
    if not check_prerequisites():
        return 1
    
    runner = TestSuiteRunner(verbose=args.verbose)
    
    # Step 1: Fetch fresh data if requested or if no data file exists
    if args.fetch_data or not os.path.exists('aave_v3_data.json'):
        runner.log("📥 Fetching fresh data for tests...")
        success, output = runner.run_script('aave_fetcher.py', ['--turbo', '--validate'])
        
        if not success:
            runner.log("❌ Failed to fetch data - some tests may fail")
        else:
            runner.log("✅ Fresh data fetched successfully")
    
    # Step 2: Run test suites based on arguments
    if not args.validation_only and not args.integration_only:
        # Run all tests
        runner.log("🚀 Running complete test suite...")
        
        # Core functionality tests
        test_args = ['--save-reports'] if args.save_reports else []
        if args.quick:
            test_args.append('--quick')
        
        runner.run_script('test_runner.py', test_args)
        
        # Protocol parameter validation
        validation_args = ['--verbose'] if args.verbose else []
        if args.save_reports:
            validation_args.append('--save-report')
        
        runner.run_script('validate_protocol_parameters.py', validation_args)
        
        # 2025 parameter validation
        runner.run_script('validate_2025_parameters.py', validation_args)
        
        # Integration tests
        integration_args = []
        if args.quick:
            integration_args.append('--quick')
        if args.save_reports:
            integration_args.append('--save-outputs')
        
        runner.run_script('test_workflow_integration.py', integration_args)
    
    elif args.validation_only:
        # Run validation tests only
        runner.log("🔍 Running validation tests only...")
        
        validation_args = ['--verbose'] if args.verbose else []
        if args.save_reports:
            validation_args.append('--save-report')
        
        runner.run_script('validate_protocol_parameters.py', validation_args)
        runner.run_script('validate_2025_parameters.py', validation_args)
        
        # Run core test runner in validation-only mode
        test_args = ['--validation-only']
        if args.save_reports:
            test_args.append('--save-reports')
        
        runner.run_script('test_runner.py', test_args)
    
    elif args.integration_only:
        # Run integration tests only
        runner.log("🔗 Running integration tests only...")
        
        integration_args = []
        if args.quick:
            integration_args.append('--quick')
        else:
            integration_args.append('--full')
        if args.save_reports:
            integration_args.append('--save-outputs')
        
        runner.run_script('test_workflow_integration.py', integration_args)
    
    # Print final summary
    success = runner.print_summary()
    
    if success:
        runner.log("🎉 All tests completed successfully!")
        return 0
    else:
        runner.log("❌ Some tests failed - check output above")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)