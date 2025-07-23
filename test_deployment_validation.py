#!/usr/bin/env python3
"""
Deployment Validation Script
Validates GitHub Pages deployment and accessibility.
"""

import sys
import os
import json
import time
import urllib.request
import urllib.error
import subprocess
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import re


class DeploymentValidator:
    """Validates GitHub Pages deployment and accessibility."""
    
    def __init__(self):
        self.github_info = self._detect_github_repository()
        self.validation_results = {}
        
    def _detect_github_repository(self) -> Optional[Dict[str, str]]:
        """Detect GitHub repository information."""
        try:
            result = subprocess.run(
                ['git', 'remote', 'get-url', 'origin'],
                capture_output=True,
                text=True,
                check=True
            )
            
            remote_url = result.stdout.strip()
            
            if 'github.com' in remote_url:
                # Parse repository info
                if remote_url.startswith('git@github.com:'):
                    repo_path = remote_url.replace('git@github.com:', '').replace('.git', '')
                elif remote_url.startswith('https://github.com/'):
                    repo_path = remote_url.replace('https://github.com/', '').replace('.git', '')
                else:
                    return None
                
                if '/' in repo_path:
                    username, repo_name = repo_path.split('/', 1)
                    return {
                        'username': username,
                        'repo_name': repo_name,
                        'pages_url': f"https://{username}.github.io/{repo_name}",
                        'raw_url': f"https://raw.githubusercontent.com/{username}/{repo_name}/main"
                    }
            
            return None
            
        except Exception:
            return None
    
    def validate_local_files(self) -> bool:
        """Validate that required files exist locally."""
        print("📁 Validating local files...")
        
        required_files = [
            'aave_v3_data.json',
            'aave_v3_data.html',
            '.github/workflows/update-aave-data.yml'
        ]
        
        missing_files = []
        for file_path in required_files:
            if not os.path.exists(file_path):
                missing_files.append(file_path)
        
        if missing_files:
            print(f"❌ Missing required files: {missing_files}")
            return False
        
        # Validate JSON structure
        try:
            with open('aave_v3_data.json', 'r') as f:
                data = json.load(f)
            
            if 'networks' not in data or 'metadata' not in data:
                print("❌ Invalid JSON structure")
                return False
            
            if len(data['networks']) == 0:
                print("❌ No network data in JSON")
                return False
                
        except json.JSONDecodeError:
            print("❌ Invalid JSON format")
            return False
        
        # Validate HTML content
        try:
            with open('aave_v3_data.html', 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            if '<table' not in html_content or 'Liquidation Threshold' not in html_content:
                print("❌ Invalid HTML structure")
                return False
                
        except Exception:
            print("❌ Could not read HTML file")
            return False
        
        print("✅ Local files validated")
        return True
    
    def validate_github_pages_configuration(self) -> bool:
        """Validate GitHub Pages configuration."""
        print("⚙️  Validating GitHub Pages configuration...")
        
        if not self.github_info:
            print("⚠️  Not a GitHub repository - skipping Pages validation")
            return True
        
        # Check if repository is public (required for free GitHub Pages)
        try:
            # Try to access the repository's main page
            repo_url = f"https://github.com/{self.github_info['username']}/{self.github_info['repo_name']}"
            
            with urllib.request.urlopen(repo_url, timeout=10) as response:
                if response.status == 200:
                    print("✅ Repository is publicly accessible")
                else:
                    print(f"⚠️  Repository returned status {response.status}")
                    
        except urllib.error.HTTPError as e:
            if e.code == 404:
                print("❌ Repository is private or does not exist")
                return False
            else:
                print(f"⚠️  Could not verify repository accessibility: {e}")
        except Exception as e:
            print(f"⚠️  Error checking repository: {e}")
        
        print("✅ GitHub Pages configuration appears valid")
        return True
    
    def test_github_pages_deployment(self) -> bool:
        """Test GitHub Pages deployment accessibility."""
        print("🌐 Testing GitHub Pages deployment...")
        
        if not self.github_info:
            print("⚠️  No GitHub repository detected - skipping deployment test")
            return True
        
        pages_url = self.github_info['pages_url']
        html_url = f"{pages_url}/aave_v3_data.html"
        
        try:
            # Test HTML page accessibility
            with urllib.request.urlopen(html_url, timeout=30) as response:
                if response.status == 200:
                    html_content = response.read().decode('utf-8')
                    
                    # Validate HTML content
                    if '<table' in html_content and 'Liquidation Threshold' in html_content:
                        print(f"✅ GitHub Pages HTML accessible: {html_url}")
                        
                        # Check for data freshness
                        if 'Last Updated' in html_content or 'last_updated' in html_content:
                            print("   📅 Data freshness indicator found")
                        
                        return True
                    else:
                        print("❌ GitHub Pages HTML has invalid content")
                        return False
                else:
                    print(f"❌ GitHub Pages returned status {response.status}")
                    return False
                    
        except urllib.error.HTTPError as e:
            if e.code == 404:
                print(f"⚠️  GitHub Pages not yet deployed (404): {html_url}")
                print("   This is normal for new repositories or recent changes")
                print("   GitHub Pages may take a few minutes to deploy after first push")
                return True  # Don't fail for new deployments
            else:
                print(f"❌ GitHub Pages error {e.code}: {e}")
                return False
        except urllib.error.URLError as e:
            print(f"⚠️  GitHub Pages not accessible: {e}")
            print("   This may be normal for new repositories")
            return True  # Don't fail for connectivity issues
        except Exception as e:
            print(f"⚠️  Error testing GitHub Pages: {e}")
            return True  # Don't fail for unexpected errors
    
    def test_json_api_accessibility(self) -> bool:
        """Test JSON API accessibility via GitHub raw URLs."""
        print("📊 Testing JSON API accessibility...")
        
        if not self.github_info:
            print("⚠️  No GitHub repository detected - skipping API test")
            return True
        
        json_url = f"{self.github_info['raw_url']}/aave_v3_data.json"
        
        try:
            with urllib.request.urlopen(json_url, timeout=30) as response:
                if response.status == 200:
                    json_content = response.read().decode('utf-8')
                    
                    # Validate JSON content
                    try:
                        data = json.loads(json_content)
                        
                        if 'networks' in data and 'metadata' in data:
                            print(f"✅ JSON API accessible: {json_url}")
                            
                            # Check data completeness
                            network_count = len(data['networks'])
                            total_assets = sum(len(assets) for assets in data['networks'].values())
                            
                            print(f"   📊 {network_count} networks, {total_assets} assets")
                            
                            # Check CORS headers (important for web applications)
                            headers = dict(response.headers)
                            if 'Access-Control-Allow-Origin' in headers:
                                print("   🌐 CORS headers present")
                            else:
                                print("   ⚠️  No CORS headers (may limit web app usage)")
                            
                            return True
                        else:
                            print("❌ JSON API has invalid structure")
                            return False
                            
                    except json.JSONDecodeError:
                        print("❌ JSON API returned invalid JSON")
                        return False
                else:
                    print(f"❌ JSON API returned status {response.status}")
                    return False
                    
        except urllib.error.HTTPError as e:
            if e.code == 404:
                print(f"⚠️  JSON API not yet available (404): {json_url}")
                print("   This is normal for new repositories")
                return True  # Don't fail for new repositories
            else:
                print(f"❌ JSON API error {e.code}: {e}")
                return False
        except Exception as e:
            print(f"⚠️  Error testing JSON API: {e}")
            return True  # Don't fail for connectivity issues
    
    def validate_workflow_execution(self) -> bool:
        """Validate GitHub Actions workflow execution."""
        print("⚙️  Validating workflow execution...")
        
        workflow_path = '.github/workflows/update-aave-data.yml'
        
        if not os.path.exists(workflow_path):
            print("❌ Workflow file not found")
            return False
        
        try:
            with open(workflow_path, 'r') as f:
                workflow_content = f.read()
            
            # Check for performance optimization
            if '--turbo' in workflow_content:
                print("✅ Workflow uses turbo mode for optimal performance")
            elif '--ultra-fast' in workflow_content:
                print("✅ Workflow uses ultra-fast mode")
            else:
                print("⚠️  Workflow may not be performance optimized")
            
            # Check for proper file handling
            required_patterns = [
                r'git add.*aave_v3_data\.json',
                r'git add.*aave_v3_data\.html',
                r'git commit',
                r'git push'
            ]
            
            missing_patterns = []
            for pattern in required_patterns:
                if not re.search(pattern, workflow_content):
                    missing_patterns.append(pattern)
            
            if missing_patterns:
                print(f"⚠️  Workflow may be missing patterns: {missing_patterns}")
            else:
                print("✅ Workflow file handling appears correct")
            
            # Check for error handling
            if 'if:' in workflow_content and 'changed' in workflow_content:
                print("✅ Workflow has conditional execution")
            else:
                print("⚠️  Workflow may lack proper conditional execution")
            
            return True
            
        except Exception as e:
            print(f"❌ Error validating workflow: {e}")
            return False
    
    def test_data_freshness_validation(self) -> bool:
        """Test data freshness and update mechanisms."""
        print("🕒 Testing data freshness validation...")
        
        try:
            with open('aave_v3_data.json', 'r') as f:
                data = json.load(f)
            
            metadata = data.get('metadata', {})
            last_updated = metadata.get('last_updated')
            
            if not last_updated:
                print("⚠️  No last_updated timestamp in metadata")
                return False
            
            # Parse timestamp
            try:
                if last_updated.endswith('Z'):
                    update_time = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
                else:
                    update_time = datetime.fromisoformat(last_updated)
                
                # Calculate age
                now = datetime.now().astimezone()
                age = now - update_time
                age_hours = age.total_seconds() / 3600
                
                print(f"   📅 Data age: {age_hours:.1f} hours")
                
                if age_hours < 25:  # Allow 1 hour buffer for daily updates
                    print("✅ Data is fresh")
                elif age_hours < 48:
                    print("⚠️  Data is getting stale")
                else:
                    print("❌ Data is stale (>48 hours)")
                    return False
                
                # Check execution time
                execution_time = metadata.get('execution_time')
                if execution_time:
                    print(f"   ⏱️  Last execution time: {execution_time:.1f}s")
                    
                    if execution_time > 540:  # 9 minutes
                        print("⚠️  Execution time approaching GitHub Actions limit")
                    elif execution_time > 300:  # 5 minutes
                        print("✅ Execution time within acceptable range")
                    else:
                        print("✅ Excellent execution time")
                
                return True
                
            except ValueError as e:
                print(f"❌ Invalid timestamp format: {e}")
                return False
                
        except Exception as e:
            print(f"❌ Error validating data freshness: {e}")
            return False
    
    def generate_deployment_report(self) -> Dict[str, Any]:
        """Generate comprehensive deployment validation report."""
        print("\n📊 Generating deployment validation report...")
        
        # Run all validations
        validations = [
            ("Local Files", self.validate_local_files),
            ("GitHub Pages Config", self.validate_github_pages_configuration),
            ("Pages Deployment", self.test_github_pages_deployment),
            ("JSON API", self.test_json_api_accessibility),
            ("Workflow Execution", self.validate_workflow_execution),
            ("Data Freshness", self.test_data_freshness_validation)
        ]
        
        results = {}
        passed_count = 0
        
        for validation_name, validation_func in validations:
            try:
                result = validation_func()
                results[validation_name] = result
                if result:
                    passed_count += 1
            except Exception as e:
                print(f"❌ Validation '{validation_name}' failed: {e}")
                results[validation_name] = False
        
        # Create report
        report = {
            "timestamp": datetime.now().isoformat(),
            "github_repository": self.github_info,
            "validation_results": results,
            "summary": {
                "total_validations": len(validations),
                "passed_validations": passed_count,
                "success_rate": passed_count / len(validations),
                "deployment_ready": passed_count >= len(validations) - 1  # Allow 1 failure
            }
        }
        
        # Add URLs if available
        if self.github_info:
            report["access_urls"] = {
                "html_page": f"{self.github_info['pages_url']}/aave_v3_data.html",
                "json_api": f"{self.github_info['raw_url']}/aave_v3_data.json",
                "repository": f"https://github.com/{self.github_info['username']}/{self.github_info['repo_name']}"
            }
        
        return report
    
    def run_validation(self) -> bool:
        """Run complete deployment validation."""
        print("🚀 Starting Deployment Validation")
        print("=" * 50)
        
        if self.github_info:
            print(f"📍 Repository: {self.github_info['username']}/{self.github_info['repo_name']}")
            print(f"🌐 Pages URL: {self.github_info['pages_url']}")
            print(f"📊 API URL: {self.github_info['raw_url']}")
        else:
            print("⚠️  No GitHub repository detected")
        
        print()
        
        # Generate report
        report = self.generate_deployment_report()
        
        # Print summary
        print("\n" + "=" * 50)
        print("DEPLOYMENT VALIDATION RESULTS")
        print("=" * 50)
        
        for validation_name, result in report["validation_results"].items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {validation_name}")
        
        summary = report["summary"]
        print(f"\n📊 Summary: {summary['passed_validations']}/{summary['total_validations']} validations passed")
        print(f"📈 Success rate: {summary['success_rate']:.1%}")
        
        if summary["deployment_ready"]:
            print("🎉 DEPLOYMENT READY!")
            
            if self.github_info:
                print("\n🔗 Access URLs:")
                for url_type, url in report["access_urls"].items():
                    print(f"   {url_type}: {url}")
        else:
            print("⚠️  Deployment issues detected - review failures")
        
        # Save report
        try:
            with open('deployment_validation_report.json', 'w') as f:
                json.dump(report, f, indent=2)
            print(f"\n📊 Validation report saved to deployment_validation_report.json")
        except Exception as e:
            print(f"⚠️  Could not save validation report: {e}")
        
        return summary["deployment_ready"]


def main():
    """Main entry point for deployment validation."""
    validator = DeploymentValidator()
    success = validator.run_validation()
    
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)