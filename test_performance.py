#!/usr/bin/env python3
"""
Performance test script to compare different fetching strategies.
"""

import subprocess
import time
import json
import sys


def run_fetch_test(mode: str, args: list) -> dict:
    """Run a fetch test and return performance metrics."""
    print(f"\n{'='*60}")
    print(f"Testing: {mode}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    cmd = ["python", "aave_fetcher.py"] + args + ["--skip-reports"]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        
        elapsed = time.time() - start_time
        
        if result.returncode == 0:
            # Try to extract metrics from output
            lines = result.stdout.split('\n')
            total_assets = 0
            networks_success = 0
            
            for line in lines:
                if "Total assets:" in line or "assets" in line and "✅" in line:
                    try:
                        # Extract number from line
                        import re
                        numbers = re.findall(r'\d+', line)
                        if numbers:
                            for num in numbers:
                                if int(num) > 50:  # Likely to be total assets
                                    total_assets = int(num)
                                    break
                    except:
                        pass
                
                if "Successful networks:" in line:
                    try:
                        parts = line.split(":")[-1].strip().split("/")
                        networks_success = int(parts[0])
                    except:
                        pass
            
            # Check if output file exists and get asset count
            try:
                with open('aave_v3_data.json', 'r') as f:
                    data = json.load(f)
                    if 'data' in data:
                        total_assets = sum(len(assets) for assets in data['data'].values())
                        networks_success = len(data['data'])
            except:
                pass
            
            return {
                'mode': mode,
                'success': True,
                'elapsed_time': elapsed,
                'total_assets': total_assets,
                'networks_success': networks_success,
                'assets_per_second': total_assets / elapsed if elapsed > 0 and total_assets > 0 else 0
            }
        else:
            return {
                'mode': mode,
                'success': False,
                'elapsed_time': elapsed,
                'error': result.stderr[:200]
            }
            
    except subprocess.TimeoutExpired:
        return {
            'mode': mode,
            'success': False,
            'elapsed_time': 600,
            'error': 'Timeout after 10 minutes'
        }
    except Exception as e:
        return {
            'mode': mode,
            'success': False,
            'elapsed_time': time.time() - start_time,
            'error': str(e)
        }


def main():
    """Run performance comparison tests."""
    print("🚀 AAVE FETCHER PERFORMANCE COMPARISON")
    print("=====================================")
    
    tests = [
        ("Turbo Mode (Recommended)", ["--turbo"]),
        ("Ultra-Fast Mode (Multicall3)", ["--ultra-fast", "--max-workers", "10"]),
        ("Parallel Mode (Original)", ["--parallel", "--max-workers", "4"]),
        ("Sequential Mode", ["--sequential"])
    ]
    
    results = []
    
    # Run tests
    for mode, args in tests:
        result = run_fetch_test(mode, args)
        results.append(result)
        
        if result['success']:
            print(f"✅ Success in {result['elapsed_time']:.1f}s")
            if result['total_assets'] > 0:
                print(f"   - {result['total_assets']} assets from {result['networks_success']} networks")
                print(f"   - {result['assets_per_second']:.1f} assets/second")
        else:
            print(f"❌ Failed: {result.get('error', 'Unknown error')}")
    
    # Print comparison summary
    print(f"\n{'='*60}")
    print("PERFORMANCE SUMMARY")
    print(f"{'='*60}")
    
    successful_results = [r for r in results if r['success'] and r['total_assets'] > 0]
    
    if successful_results:
        # Sort by performance (assets per second)
        successful_results.sort(key=lambda x: x['assets_per_second'], reverse=True)
        
        print("\nRanking by speed (assets/second):")
        for i, result in enumerate(successful_results):
            print(f"{i+1}. {result['mode']:30} {result['assets_per_second']:8.1f} assets/s ({result['elapsed_time']:.1f}s total)")
        
        # Calculate speedup
        if len(successful_results) > 1:
            fastest = successful_results[0]
            slowest = successful_results[-1]
            
            speedup = slowest['elapsed_time'] / fastest['elapsed_time']
            
            print(f"\n🚀 {fastest['mode']} is {speedup:.1f}x faster than {slowest['mode']}")
            
            # Performance improvement percentage
            improvement = ((slowest['elapsed_time'] - fastest['elapsed_time']) / slowest['elapsed_time']) * 100
            print(f"   Performance improvement: {improvement:.0f}%")
    
    else:
        print("❌ No successful test runs to compare")


if __name__ == "__main__":
    main()