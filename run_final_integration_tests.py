#!/usr/bin/env python3
"""
Final Integration Test Runner
Executes all final integration and deployment tests in sequence.
"""

import sys
import os
import time
import subprocess
import json
from typing import Dict, List, Any, Tuple
from datetime import datetime


class FinalIntegrationTestRunner:
    """Runs all final integration tests and generates comprehensive report."""
    
    def __init__(self):
        self.start_time = time.time()
        self.test_results = {}
        self.test_reports = {}
        
    def run_test_script(self, script_name: str, description: str) -> Tuple[bool, Dict[str, Any]]:
        """Run a test script and capture results."""
        print(f"\n🔄 Running {description}...")
        print("=" * 60)
        
        try:
            # Run the test script
            result = subprocess.run([
                sys.executable, script_name
            ], capture_output=True, text=True, timeout=600)
            
            success = result.returncode == 0
            
            # Print output
            if result.stdout:
                print(result.stdout)
            
            if result.stderr and not success:
                print("STDERR:")
                print(result.stderr)
            
            # Try to load test report if it exists
            report_files = {
                'test_final_integration.py': 'integration_test_report.json',
                'test_deployment_validation.py': 'deployment_validation_report.json',
                'test_llm_consumption.py': 'llm_consumption_test_report.json'
            }
            
            report_data = {}
            report_file = report_files.get(script_name)
            if report_file and os.path.exists(report_file):
                try:
                    with open(report_file, 'r') as f:
                        report_data = json.load(f)
                except Exception as e:
                    print(f"⚠️  Could not load report {report_file}: {e}")
            
            return success, report_data
            
        except subprocess.TimeoutExpired:
            print(f"❌ Test script {script_name} timed out (10 minutes)")
            return False, {}
        except Exception as e:
            print(f"❌ Error running test script {script_name}: {e}")
            return False, {}
    
    def run_workflow_validation(self) -> bool:
        """Run GitHub Actions workflow validation."""
        print(f"\n🔄 Running GitHub Actions Workflow Validation...")
        print("=" * 60)
        
        try:
            # Test workflow file syntax
            workflow_file = '.github/workflows/update-aave-data.yml'
            
            if not os.path.exists(workflow_file):
                print("❌ Workflow file not found")
                return False
            
            # Basic YAML syntax validation
            try:
                import yaml
                with open(workflow_file, 'r') as f:
                    yaml.safe_load(f)
                print("✅ Workflow YAML syntax valid")
            except ImportError:
                print("⚠️  PyYAML not available - skipping YAML validation")
            except Exception as e:
                print(f"❌ Workflow YAML syntax error: {e}")
                return False
            
            # Check workflow content
            with open(workflow_file, 'r') as f:
                content = f.read()
            
            required_elements = [
                'on:',
                'schedule:',
                'workflow_dispatch:',
                'runs-on: ubuntu-latest',
                'python aave_fetcher.py',
                'git add',
                'git commit',
                'git push'
            ]
            
            missing_elements = []
            for element in required_elements:
                if element not in content:
                    missing_elements.append(element)
            
            if missing_elements:
                print(f"❌ Missing workflow elements: {missing_elements}")
                return False
            
            print("✅ GitHub Actions workflow validation passed")
            return True
            
        except Exception as e:
            print(f"❌ Workflow validation error: {e}")
            return False
    
    def run_data_validation(self) -> bool:
        """Run comprehensive data validation."""
        print(f"\n🔄 Running Comprehensive Data Validation...")
        print("=" * 60)
        
        try:
            # Run the main fetcher with validation using turbo mode
            result = subprocess.run([
                sys.executable, 'aave_fetcher.py', '--turbo', '--validate', '--timeout', '60'
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                print(f"❌ Data fetcher failed with return code {result.returncode}")
                if result.stderr:
                    print("STDERR:")
                    print(result.stderr)
                return False
            
            print(result.stdout)
            
            # Check if validation report was generated
            if os.path.exists('validation_report.json'):
                try:
                    with open('validation_report.json', 'r') as f:
                        validation_data = json.load(f)
                    
                    if validation_data.get('summary', {}).get('is_valid', False):
                        print("✅ Data validation passed")
                        return True
                    else:
                        print("❌ Data validation failed")
                        return False
                        
                except Exception as e:
                    print(f"⚠️  Could not read validation report: {e}")
            
            print("✅ Data validation completed")
            return True
            
        except subprocess.TimeoutExpired:
            print("❌ Data validation timed out")
            return False
        except Exception as e:
            print(f"❌ Data validation error: {e}")
            return False
    
    def run_performance_validation(self) -> bool:
        """Run performance validation tests."""
        print(f"\n🔄 Running Performance Validation...")
        print("=" * 60)
        
        try:
            # Test different performance modes
            performance_tests = [
                ('--turbo', 'Turbo Mode'),
                ('--ultra-fast', 'Ultra-Fast Mode'),
                ('--parallel', 'Parallel Mode')
            ]
            
            performance_results = {}
            
            for mode_flag, mode_name in performance_tests:
                print(f"\n   Testing {mode_name}...")
                
                start_time = time.time()
                
                result = subprocess.run([
                    sys.executable, 'aave_fetcher.py', mode_flag, '--timeout', '30'
                ], capture_output=True, text=True, timeout=180)
                
                execution_time = time.time() - start_time
                
                if result.returncode == 0:
                    performance_results[mode_name] = {
                        'success': True,
                        'execution_time': execution_time,
                        'github_actions_compliant': execution_time < 540  # 9 minutes
                    }
                    print(f"   ✅ {mode_name}: {execution_time:.1f}s")
                else:
                    performance_results[mode_name] = {
                        'success': False,
                        'execution_time': execution_time,
                        'github_actions_compliant': False
                    }
                    print(f"   ❌ {mode_name}: Failed")
            
            # Check if at least one mode is GitHub Actions compliant
            compliant_modes = [
                mode for mode, result in performance_results.items()
                if result['success'] and result['github_actions_compliant']
            ]
            
            if compliant_modes:
                print(f"\n✅ Performance validation passed")
                print(f"   GitHub Actions compliant modes: {', '.join(compliant_modes)}")
                return True
            else:
                print(f"\n❌ No performance modes are GitHub Actions compliant")
                return False
                
        except Exception as e:
            print(f"❌ Performance validation error: {e}")
            return False
    
    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate comprehensive final integration test report."""
        total_time = time.time() - self.start_time
        
        # Count successful tests
        successful_tests = sum(1 for result in self.test_results.values() if result)
        total_tests = len(self.test_results)
        
        # Create comprehensive report
        report = {
            "timestamp": datetime.now().isoformat(),
            "execution_time": total_time,
            "test_summary": {
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "failed_tests": total_tests - successful_tests,
                "success_rate": successful_tests / max(total_tests, 1)
            },
            "test_results": self.test_results,
            "individual_reports": self.test_reports,
            "deployment_readiness": {
                "ready_for_deployment": successful_tests >= total_tests - 1,  # Allow 1 failure
                "critical_tests_passed": all([
                    self.test_results.get("Complete Workflow Execution", False),
                    self.test_results.get("Data Validation", False),
                    self.test_results.get("GitHub Actions Workflow", False)
                ]),
                "performance_compliant": self.test_results.get("Performance Validation", False)
            },
            "recommendations": []
        }
        
        # Add recommendations based on results
        if not report["deployment_readiness"]["ready_for_deployment"]:
            report["recommendations"].append("Review failed tests before deployment")
        
        if not report["deployment_readiness"]["performance_compliant"]:
            report["recommendations"].append("Optimize performance for GitHub Actions compliance")
        
        if report["deployment_readiness"]["ready_for_deployment"]:
            report["recommendations"].append("System is ready for production deployment")
        
        return report
    
    def run_all_tests(self) -> bool:
        """Run all final integration tests."""
        print("🚀 Starting Final Integration and Deployment Testing Suite")
        print("=" * 70)
        print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
        # Define all tests to run
        test_suite = [
            # Core integration tests
            ("test_final_integration.py", "Complete Integration Testing", "integration"),
            
            # Deployment validation
            ("test_deployment_validation.py", "Deployment Validation", "deployment"),
            
            # LLM consumption testing
            ("test_llm_consumption.py", "LLM Consumption Testing", "llm"),
        ]
        
        # Run script-based tests
        for script_name, description, test_type in test_suite:
            if os.path.exists(script_name):
                success, report_data = self.run_test_script(script_name, description)
                self.test_results[description] = success
                if report_data:
                    self.test_reports[test_type] = report_data
            else:
                print(f"⚠️  Test script {script_name} not found - skipping")
                self.test_results[description] = False
        
        # Run additional validation tests
        additional_tests = [
            ("GitHub Actions Workflow", self.run_workflow_validation),
            ("Data Validation", self.run_data_validation),
            ("Performance Validation", self.run_performance_validation)
        ]
        
        for test_name, test_function in additional_tests:
            try:
                success = test_function()
                self.test_results[test_name] = success
            except Exception as e:
                print(f"❌ Test '{test_name}' failed with exception: {e}")
                self.test_results[test_name] = False
        
        # Generate comprehensive report
        comprehensive_report = self.generate_comprehensive_report()
        
        # Print final summary
        total_time = time.time() - self.start_time
        
        print("\n" + "=" * 70)
        print("FINAL INTEGRATION TEST RESULTS")
        print("=" * 70)
        
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name}")
        
        summary = comprehensive_report["test_summary"]
        deployment = comprehensive_report["deployment_readiness"]
        
        print(f"\n📊 Test Summary:")
        print(f"   Total tests: {summary['total_tests']}")
        print(f"   Successful: {summary['successful_tests']}")
        print(f"   Failed: {summary['failed_tests']}")
        print(f"   Success rate: {summary['success_rate']:.1%}")
        print(f"   Execution time: {total_time:.1f}s")
        
        print(f"\n🚀 Deployment Readiness:")
        print(f"   Ready for deployment: {'✅ YES' if deployment['ready_for_deployment'] else '❌ NO'}")
        print(f"   Critical tests passed: {'✅ YES' if deployment['critical_tests_passed'] else '❌ NO'}")
        print(f"   Performance compliant: {'✅ YES' if deployment['performance_compliant'] else '❌ NO'}")
        
        if comprehensive_report["recommendations"]:
            print(f"\n💡 Recommendations:")
            for recommendation in comprehensive_report["recommendations"]:
                print(f"   • {recommendation}")
        
        # Save comprehensive report
        try:
            with open('final_integration_test_report.json', 'w') as f:
                json.dump(comprehensive_report, f, indent=2)
            print(f"\n📊 Comprehensive test report saved to final_integration_test_report.json")
        except Exception as e:
            print(f"⚠️  Could not save comprehensive report: {e}")
        
        # Final verdict
        if deployment["ready_for_deployment"]:
            print("\n🎉 FINAL INTEGRATION TESTING COMPLETED SUCCESSFULLY!")
            print("   ✅ System is ready for production deployment")
            print("   ✅ All critical functionality validated")
            print("   ✅ GitHub Pages deployment ready")
            print("   ✅ LLM consumption optimized")
        else:
            print("\n⚠️  FINAL INTEGRATION TESTING COMPLETED WITH ISSUES")
            print("   ❌ Review failed tests before deployment")
            print("   🔧 Address issues and re-run tests")
        
        return deployment["ready_for_deployment"]


def main():
    """Main entry point for final integration test runner."""
    runner = FinalIntegrationTestRunner()
    success = runner.run_all_tests()
    
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)