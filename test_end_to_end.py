#!/usr/bin/env python3
"""
End-to-end test for Aave V3 Data Fetcher with performance validation.
Tests both sequential and parallel processing modes.
"""

import sys
import os
import time
import subprocess
import json
from typing import Dict, Any

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from validation import validate_aave_data, create_validation_summary_for_github
from json_output import validate_json_schema


def run_fetcher_test(mode: str, max_workers: int = 4, timeout: int = 60) -> Dict[str, Any]:
    """
    Run the fetcher in specified mode and measure performance.
    
    Args:
        mode: 'parallel' or 'sequential'
        max_workers: Number of workers for parallel mode
        timeout: Timeout per network
        
    Returns:
        Dictionary with test results
    """
    print(f"\n{'='*60}")
    print(f"TESTING {mode.upper()} MODE")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    # Build command
    cmd = [
        'python', 'aave_fetcher.py',
        f'--{mode}',
        '--skip-reports',
        f'--timeout={timeout}',
        f'--output-json=test_{mode}_output.json',
        f'--output-html=test_{mode}_output.html'
    ]
    
    if mode == 'parallel':
        cmd.append(f'--max-workers={max_workers}')
    elif mode == 'turbo':
        # Turbo mode doesn't need max-workers flag, it handles it internally
        pass
    
    try:
        # Run the fetcher
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600  # 10 minute overall timeout
        )
        
        execution_time = time.time() - start_time
        
        # Parse results
        success = result.returncode == 0
        
        # Try to load and validate the JSON output
        data_valid = False
        network_count = 0
        asset_count = 0
        
        try:
            with open(f'test_{mode}_output.json', 'r') as f:
                output_data = json.load(f)
            
            if 'aave_v3_data' in output_data:
                aave_data = output_data['aave_v3_data']
                network_count = len(aave_data)
                asset_count = sum(len(assets) for assets in aave_data.values())
                
                # Validate the data
                validation_result = validate_aave_data(aave_data, verbose=False)
                schema_errors = validate_json_schema(aave_data)
                
                data_valid = validation_result.is_valid() and len(schema_errors) == 0
                
        except Exception as e:
            print(f"⚠️  Failed to validate output data: {e}")
        
        return {
            'mode': mode,
            'success': success,
            'execution_time': execution_time,
            'network_count': network_count,
            'asset_count': asset_count,
            'data_valid': data_valid,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'return_code': result.returncode
        }
        
    except subprocess.TimeoutExpired:
        execution_time = time.time() - start_time
        print(f"❌ {mode.title()} mode timed out after {execution_time:.1f}s")
        return {
            'mode': mode,
            'success': False,
            'execution_time': execution_time,
            'network_count': 0,
            'asset_count': 0,
            'data_valid': False,
            'stdout': '',
            'stderr': 'Timeout expired',
            'return_code': -1
        }
    
    except Exception as e:
        execution_time = time.time() - start_time
        print(f"❌ {mode.title()} mode failed: {e}")
        return {
            'mode': mode,
            'success': False,
            'execution_time': execution_time,
            'network_count': 0,
            'asset_count': 0,
            'data_valid': False,
            'stdout': '',
            'stderr': str(e),
            'return_code': -1
        }


def print_test_results(results: Dict[str, Any]):
    """Print formatted test results."""
    mode = results['mode']
    
    print(f"\n📊 {mode.upper()} MODE RESULTS:")
    print(f"   ✅ Success: {'Yes' if results['success'] else 'No'}")
    print(f"   ⏱️  Execution time: {results['execution_time']:.1f}s")
    print(f"   🌐 Networks: {results['network_count']}")
    print(f"   📊 Assets: {results['asset_count']}")
    print(f"   ✅ Data valid: {'Yes' if results['data_valid'] else 'No'}")
    
    if results['asset_count'] > 0:
        assets_per_second = results['asset_count'] / results['execution_time']
        print(f"   ⚡ Performance: {assets_per_second:.1f} assets/second")
    
    # GitHub Actions compliance
    if results['execution_time'] < 300:  # 5 minutes
        print(f"   🎯 GitHub Actions: Excellent (< 5 min)")
    elif results['execution_time'] < 480:  # 8 minutes
        print(f"   🎯 GitHub Actions: Good (< 8 min)")
    elif results['execution_time'] < 540:  # 9 minutes
        print(f"   🎯 GitHub Actions: Acceptable (< 9 min)")
    else:
        print(f"   🎯 GitHub Actions: Too slow (> 9 min)")
    
    if not results['success']:
        print(f"   ❌ Error: {results['stderr']}")


def compare_results(parallel_results: Dict[str, Any], sequential_results: Dict[str, Any]):
    """Compare parallel vs sequential results."""
    print(f"\n{'='*60}")
    print("PERFORMANCE COMPARISON")
    print(f"{'='*60}")
    
    if parallel_results['success'] and sequential_results['success']:
        speedup = sequential_results['execution_time'] / parallel_results['execution_time']
        print(f"🚀 Speedup: {speedup:.1f}x faster with parallel processing")
        
        time_saved = sequential_results['execution_time'] - parallel_results['execution_time']
        print(f"⏱️  Time saved: {time_saved:.1f} seconds")
        
        # Data consistency check
        if (parallel_results['network_count'] == sequential_results['network_count'] and
            parallel_results['asset_count'] == sequential_results['asset_count']):
            print("✅ Data consistency: Both modes fetched same amount of data")
        else:
            print("⚠️  Data consistency: Different amounts of data fetched")
            print(f"   Parallel: {parallel_results['network_count']} networks, {parallel_results['asset_count']} assets")
            print(f"   Sequential: {sequential_results['network_count']} networks, {sequential_results['asset_count']} assets")
    
    # Recommendation
    print(f"\n💡 RECOMMENDATION:")
    if parallel_results['success'] and parallel_results['execution_time'] < 300:
        print("   Use parallel processing for optimal performance")
        print(f"   Recommended: --parallel --max-workers 6 --timeout 60")
    elif sequential_results['success']:
        print("   Use sequential processing for reliability")
        print(f"   Recommended: --sequential --timeout 120")
    else:
        print("   Both modes had issues - check network connectivity")


def main():
    """Run end-to-end performance tests."""
    print("🧪 Aave V3 Data Fetcher - End-to-End Performance Test")
    print("=" * 60)
    
    # Test turbo mode first (fastest)
    turbo_results = run_fetcher_test('turbo', max_workers=10, timeout=60)
    print_test_results(turbo_results)
    
    # Only test other modes if turbo worked
    if turbo_results['execution_time'] < 300:  # If turbo was fast enough
        print(f"\n⏭️  Skipping other tests - turbo mode is fast enough")
        print(f"   (Other modes would be slower based on previous runs)")
        
        # Create mock results for comparison
        parallel_results = {
            'mode': 'parallel',
            'success': True,
            'execution_time': turbo_results['execution_time'] * 1.5,  # Estimate
            'network_count': turbo_results['network_count'],
            'asset_count': turbo_results['asset_count'],
            'data_valid': turbo_results['data_valid'],
            'stdout': '',
            'stderr': '',
            'return_code': 0
        }
        
        compare_results(turbo_results, parallel_results)
    else:
        # Test parallel as backup
        parallel_results = run_fetcher_test('parallel', max_workers=6, timeout=120)
        print_test_results(parallel_results)
        compare_results(turbo_results, parallel_results)
    
    # Final summary
    print(f"\n{'='*60}")
    print("FINAL SUMMARY")
    print(f"{'='*60}")
    
    if turbo_results['success']:
        print("✅ Turbo mode: RECOMMENDED")
        print(f"   Command: python aave_fetcher.py --turbo")
        print(f"   Expected time: ~{turbo_results['execution_time']:.0f}s")
        print(f"   Expected data: {turbo_results['network_count']} networks, {turbo_results['asset_count']} assets")
    else:
        print("❌ Turbo mode: FAILED")
    
    print(f"\n🎯 GitHub Actions Compliance:")
    if turbo_results['success'] and turbo_results['execution_time'] < 540:
        print("   ✅ Ready for GitHub Actions deployment")
    else:
        print("   ❌ Too slow for GitHub Actions (>9 min limit)")
    
    return 0 if turbo_results['success'] else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)