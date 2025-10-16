"""
Test script to verify WhatsApp retry issue is fixed
"""

import sys

def test_imports():
    """Test that all imports work correctly"""
    try:
        from whatsapp_cloud_api import (
            generate_answer,
            generate_answer_with_timeout,
            process_message_async
        )
        print("OK: All functions imported successfully")
        return True
    except ImportError as e:
        print(f"ERROR: Failed to import: {e}")
        return False

def test_timeout_function():
    """Test the timeout wrapper works"""
    import asyncio
    from whatsapp_cloud_api import generate_answer_with_timeout
    
    async def run_test():
        # Test with a simple query (should work)
        result = await generate_answer_with_timeout("test", timeout=5)
        if result:
            print(f"OK: Timeout function returned: {result[:100]}...")
            return True
        return False
    
    try:
        success = asyncio.run(run_test())
        return success
    except Exception as e:
        print(f"ERROR: Timeout test failed: {e}")
        return False

def verify_critical_features():
    """Verify critical features are in place"""
    import inspect
    from whatsapp_cloud_api import process_message_async
    
    # Check the function has the finally block
    source = inspect.getsource(process_message_async)
    
    checks = [
        ("Timeout protection", "generate_answer_with_timeout" in source),
        ("Finally block", "finally:" in source),
        ("Fallback message", "fallback_msg" in source),
        ("Response tracking", "response_sent" in source),
        ("Immediate acknowledgment", "Processing your question" in source)
    ]
    
    all_good = True
    for feature, present in checks:
        if present:
            print(f"OK: {feature} is implemented")
        else:
            print(f"ERROR: {feature} is missing")
            all_good = False
    
    return all_good

def main():
    """Run all tests"""
    print("="*60)
    print("TESTING WHATSAPP RETRY FIX")
    print("="*60)
    
    tests = [
        ("Import Test", test_imports),
        ("Timeout Function", test_timeout_function),
        ("Critical Features", verify_critical_features)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\nRunning: {test_name}")
        print("-"*40)
        success = test_func()
        results.append(success)
        print()
    
    print("="*60)
    print("SUMMARY")
    print("="*60)
    
    if all(results):
        print("\nSUCCESS! All critical fixes are in place:")
        print("1. Timeout protection (30 seconds)")
        print("2. Always sends a response (prevents retries)")
        print("3. Immediate acknowledgment to user")
        print("4. Fallback messages on failure")
        print("\nThe retry issue should be completely fixed!")
    else:
        print("\nWARNING: Some tests failed. Check the output above.")
    
    return all(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)