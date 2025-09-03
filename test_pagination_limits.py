#!/usr/bin/env python3
"""
Quick test to verify page size improvements and safety features
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.pagination_config import pagination_manager, PaginationLimits

def test_pagination_limits():
    """Test pagination validation and safety features"""
    print("🧪 Testing Pagination System")
    print("=" * 50)
    
    # Test search validation
    print("\n📊 Search Validation Tests:")
    test_cases = [10, 50, 100, 200, 300]
    for size in test_cases:
        validated_size, warnings = pagination_manager.validate_page_size(size, "search")
        print(f"  Requested: {size:3d} → Validated: {validated_size:3d} | Warnings: {len(warnings)}")
        for warning in warnings:
            print(f"    ⚠️  {warning}")
    
    # Test browse validation  
    print("\n📚 Browse Validation Tests:")
    for size in test_cases + [500, 1000]:
        validated_size, warnings = pagination_manager.validate_page_size(size, "browse")
        print(f"  Requested: {size:4d} → Validated: {validated_size:3d} | Warnings: {len(warnings)}")
    
    # Test progressive loading
    print("\n⚡ Progressive Loading Tests:")
    for size in [50, 100, 150, 200]:
        should_use = pagination_manager.should_use_progressive_loading(size)
        batch_size = pagination_manager.get_batch_size(size)
        print(f"  Size: {size:3d} → Progressive: {should_use} | Batch: {batch_size}")
    
    # Test timeout calculation
    print("\n⏱️  Timeout Tests:")
    for size in [10, 50, 100, 150, 200]:
        timeout = pagination_manager.get_timeout_for_size(size)
        print(f"  Size: {size:3d} → Timeout: {timeout}s")
    
    print("\n✅ All pagination tests completed!")
    print(f"\nCurrent Limits:")
    limits = pagination_manager.limits
    print(f"  Search Max: {limits.search_results_max}")
    print(f"  Browse Max: {limits.browse_documents_max}")
    print(f"  API Default: {limits.api_default_limit}")
    print(f"  Progressive Threshold: {limits.progressive_loading_threshold}")
    print(f"  Batch Size: {limits.batch_size}")

if __name__ == "__main__":
    test_pagination_limits()
