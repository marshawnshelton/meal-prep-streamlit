"""
API Test Script
Quick test to verify your grocery price APIs are working
"""

from price_api_service import PriceAPIService
import sys


def test_api_setup():
    """Test API configuration and functionality"""
    
    print("="*60)
    print("🧪 TESTING GROCERY PRICE APIs")
    print("="*60)
    print()
    
    # Initialize service
    print("📦 Initializing PriceAPIService...")
    try:
        service = PriceAPIService()
        print("✅ Service initialized\n")
    except Exception as e:
        print(f"❌ Failed to initialize service: {e}")
        return False
    
    # Check API health
    print("🏥 Checking API Health...")
    print("-" * 60)
    status = service.health_check()
    
    print(f"  Instacart API: {'✅ Available' if status['instacart'] else '❌ Not configured'}")
    print(f"  Kroger API:    {'✅ Available' if status['kroger'] else '❌ Not configured'}")
    print(f"  Fallback Mode: {'✅ Available' if status['fallback'] else '❌ Error'}")
    print()
    
    # Test price fetching
    print("💰 Testing Price Fetching...")
    print("-" * 60)
    
    test_items = [
        ("chicken thighs", "costco"),
        ("salmon", "whole_foods"),
        ("eggs", "jewel"),
    ]
    
    for item, store in test_items:
        try:
            print(f"\nFetching: {item} at {store}")
            price_data = service.get_price(item, store, "60827")
            
            print(f"  ✅ {price_data['item']}")
            print(f"     Price: ${price_data['price']:.2f} ({price_data['unit']})")
            print(f"     Per unit: ${price_data['price_per_unit']:.2f}/{price_data['unit_type']}")
            print(f"     Source: {price_data['source']} (confidence: {price_data['confidence']})")
            print(f"     In stock: {price_data['in_stock']}")
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    print("\n" + "="*60)
    print("🎉 TEST COMPLETE")
    print("="*60)
    print()
    
    # Summary
    if status['instacart'] and status['kroger']:
        print("✅ ALL SYSTEMS GO! You have full API access.")
        print("   You'll get real-time prices from all stores.")
    elif status['instacart'] or status['kroger']:
        print("⚠️  PARTIAL API ACCESS")
        if status['instacart']:
            print("   ✅ Instacart working (Costco, Whole Foods, Pete's, Aldi)")
        if status['kroger']:
            print("   ✅ Kroger working (Jewel-Osco)")
        print("   Missing APIs will use estimates.")
    else:
        print("⚠️  NO API ACCESS - Using Estimates")
        print("   App will work, but with estimated prices.")
        print("   Set up APIs for real-time pricing.")
        print()
        print("   📖 See API_SETUP_GUIDE.md for instructions")
    
    print()
    return True


if __name__ == "__main__":
    success = test_api_setup()
    sys.exit(0 if success else 1)
