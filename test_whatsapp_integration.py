"""
Test script to verify WhatsApp integration with RAG
"""

import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_rag_import():
    """Test if RAG components can be imported"""
    try:
        from rag import RAGEngine, sanitize_response_text
        logger.info("OK: RAG module imported successfully")
        return True
    except ImportError as e:
        logger.error(f"ERROR: Failed to import RAG: {e}")
        return False

def test_conversation_manager():
    """Test if ConversationManager can be imported"""
    try:
        from conversation_manager import ConversationManager
        logger.info("OK: ConversationManager imported successfully")
        return True
    except ImportError as e:
        logger.error(f"ERROR: Failed to import ConversationManager: {e}")
        return False

def test_generate_answer():
    """Test the generate_answer function"""
    try:
        # Import the function
        from whatsapp_cloud_api import generate_answer
        logger.info("OK: generate_answer function imported")
        
        # Test questions
        test_queries = [
            "What is vitiligo?",
            "Hello",
            "How does vitiligo affect the skin?",
            "What treatments are available for vitiligo?"
        ]
        
        for query in test_queries:
            logger.info(f"\nTesting query: '{query}'")
            response = generate_answer(query, session_id="test_session")
            logger.info(f"> Response length: {len(response)} characters")
            logger.info(f"> Response preview: {response[:200]}...")
            
            # Check if response includes support link
            if "vitiligosupportgroup.com" in response:
                logger.info("LINK: Support link included in response")
            
            print(f"\nQuery: {query}")
            print(f"Response: {response[:300]}...")
            print("-" * 50)
        
        return True
        
    except Exception as e:
        logger.error(f"ERROR: Error testing generate_answer: {e}")
        return False

def test_rag_initialization():
    """Test if RAG engine initializes properly"""
    try:
        from rag import RAGEngine
        rag = RAGEngine()
        logger.info("OK: RAG engine initialized successfully")
        
        # Test a query
        result = rag.query("What is vitiligo?")
        if result and result.get("response"):
            logger.info(f"OK: RAG query successful, response length: {len(result['response'])}")
            return True
        else:
            logger.error("ERROR: RAG query returned empty response")
            return False
            
    except Exception as e:
        logger.error(f"ERROR: Failed to initialize RAG: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("WHATSAPP RAG INTEGRATION TEST")
    print("=" * 60)
    
    tests = [
        ("RAG Import", test_rag_import),
        ("ConversationManager Import", test_conversation_manager),
        ("RAG Initialization", test_rag_initialization),
        ("Generate Answer Function", test_generate_answer)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\nRunning: {test_name}")
        print("-" * 40)
        success = test_func()
        results.append((test_name, success))
        print()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    for test_name, success in results:
        status = "OK: PASSED" if success else "ERROR: FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(success for _, success in results)
    if all_passed:
        print("\nSUCCESS! All tests passed! Your WhatsApp integration is working!")
    else:
        print("\nWARNING: Some tests failed. Check the errors above.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)