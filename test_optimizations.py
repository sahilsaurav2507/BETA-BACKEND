#!/usr/bin/env python3
"""
Test script to verify all optimizations are working correctly
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_optimizations():
    """Test all optimization systems"""
    
    print("=== OPTIMIZATION SYSTEMS TEST ===")
    print()
    
    # Test 1: Force sync optimizations
    print("1. 🔄 Force syncing optimization systems...")
    try:
        response = requests.post(f"{BASE_URL}/force-sync-optimizations")
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Sync completed: {result['message']}")
            print(f"   BST Sync: {result['results']['bst_sync']}")
            print(f"   Precomputed Sync: {result['results']['precomputed_sync']}")
        else:
            print(f"   ❌ Sync failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Sync error: {e}")
    
    print()
    
    # Test 2: Test regular leaderboard (should use BST)
    print("2. 🏆 Testing regular leaderboard (BST optimization)...")
    try:
        start_time = time.time()
        response = requests.get(f"{BASE_URL}/leaderboard?page=1&limit=10")
        end_time = time.time()
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Leaderboard retrieved in {(end_time - start_time)*1000:.2f}ms")
            print(f"   Total users: {result['metadata']['total_users']}")
            print(f"   Pages: {result['pagination']['pages']}")
        else:
            print(f"   ❌ Leaderboard failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Leaderboard error: {e}")
    
    print()
    
    # Test 3: Test precomputed metrics
    print("3. 📊 Testing precomputed leaderboard metrics...")
    try:
        response = requests.get(f"{BASE_URL}/leaderboard/precompute-metrics")
        if response.status_code == 200:
            result = response.json()
            metrics = result['precomputed_metrics']
            print(f"   ✅ Precomputed metrics retrieved")
            print(f"   Cached pages: {metrics['cached_pages']}")
            print(f"   Cached user ranks: {metrics['cached_user_ranks']}")
            print(f"   Cache hit rate: {metrics['cache_hit_rate']*100:.1f}%")
            print(f"   Last computation: {metrics['last_computation_time']*1000:.2f}ms")
        else:
            print(f"   ❌ Metrics failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Metrics error: {e}")
    
    print()
    
    # Test 4: Test around-me functionality
    print("4. 🎯 Testing around-me functionality...")
    try:
        start_time = time.time()
        response = requests.get(f"{BASE_URL}/leaderboard/around-me?range=5")
        end_time = time.time()
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Around-me retrieved in {(end_time - start_time)*1000:.2f}ms")
            print(f"   Surrounding users: {len(result['surrounding_users'])}")
        else:
            print(f"   ❌ Around-me failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Around-me error: {e}")
    
    print()
    
    # Test 5: Performance comparison
    print("5. ⚡ Performance comparison test...")
    try:
        # Test regular leaderboard multiple times
        regular_times = []
        for i in range(5):
            start_time = time.time()
            response = requests.get(f"{BASE_URL}/leaderboard?page=1&limit=10")
            end_time = time.time()
            if response.status_code == 200:
                regular_times.append((end_time - start_time) * 1000)
        
        if regular_times:
            avg_time = sum(regular_times) / len(regular_times)
            print(f"   ✅ Average response time: {avg_time:.2f}ms")
            print(f"   Min: {min(regular_times):.2f}ms, Max: {max(regular_times):.2f}ms")
        
    except Exception as e:
        print(f"   ❌ Performance test error: {e}")
    
    print()
    print("=== TEST COMPLETED ===")

if __name__ == "__main__":
    test_optimizations()
