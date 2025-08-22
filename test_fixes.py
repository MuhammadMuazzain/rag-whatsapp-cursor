"""
Test script to verify the three improvements:
1. No context mentions in responses
2. FAQ filtering for doc3
3. Complete vitiligo responses with support link
"""

import json
import time
from rag import RAGEngine
from conversation_manager import ConversationManager

def test_improvements():
    print("\n" + "="*60)
    print("TESTING CHATBOT IMPROVEMENTS")
    print("="*60)
    
    # Initialize components
    print("\nInitializing RAG engine and conversation manager...")
    rag_engine = RAGEngine()
    conversation_manager = ConversationManager()
    
    # Test queries
    test_cases = [
        {
            "query": "What is vitiligo?",
            "description": "Testing vitiligo response without 'context' mentions",
            "check_for": ["context", "document", "information provided"],
            "should_not_contain": True
        },
        {
            "query": "How can I sign up for the JAK cream trial at NSC?",
            "description": "Testing doc3 response without FAQs",
            "check_for": ["Q:", "FAQs", "Can I call NSC"],
            "should_not_contain": True
        },
        {
            "query": "Tell me about vitiligo symptoms and treatment",
            "description": "Testing complete vitiligo response with support link",
            "check_for": ["vitiligosupportgroup.com"],
            "should_not_contain": False
        },
        {
            "query": "What are the eligibility criteria for the NSC trial?",
            "description": "Testing doc3 query for eligibility without FAQs",
            "check_for": ["Q:", "How long is the waiting"],
            "should_not_contain": True
        }
    ]
    
    # Run tests
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'='*50}")
        print(f"Test {i}: {test['description']}")
        print(f"Query: {test['query']}")
        print("-"*50)
        
        # Process with conversation manager
        session_id = f"test_session_{i}"
        conv_result = conversation_manager.process_message(test['query'], session_id)
        
        # Get RAG response
        result = rag_engine.query(test['query'], response_style=conv_result['response_style'])
        response = result.get("response", "")
        
        # Check if support link should be added
        if conversation_manager.should_show_support_link(test['query'], conv_result['context']):
            response += conversation_manager.support_link
            print("[OK] Support link added")
        
        # Print response
        print(f"\nResponse ({len(response)} chars):")
        print(response[:500] + "..." if len(response) > 500 else response)
        
        # Check for forbidden/required phrases
        print("\nChecking response quality:")
        response_lower = response.lower()
        
        for phrase in test['check_for']:
            phrase_lower = phrase.lower()
            if test['should_not_contain']:
                # Should NOT contain
                if phrase_lower in response_lower:
                    print(f"  [FAIL] Found '{phrase}' (should not be present)")
                else:
                    print(f"  [PASS] '{phrase}' not found")
            else:
                # Should contain
                if phrase_lower in response_lower:
                    print(f"  [PASS] Found '{phrase}'")
                else:
                    print(f"  [FAIL] '{phrase}' not found (should be present)")
        
        # Check if response is complete (not truncated mid-sentence)
        if response.endswith('...'):
            print("  [WARNING] Response may be truncated")
        elif response[-1] in '.!?':
            print("  [OK] Response ends with proper punctuation")
        
        # Check doc3 detection
        if result.get('is_doc3_query'):
            print(f"  [INFO] Doc3 query detected - using detailed style")
        
        time.sleep(1)  # Small delay between tests
    
    print(f"\n{'='*60}")
    print("TESTING COMPLETE")
    print("="*60)
    
    # Summary
    print("\nSUMMARY OF IMPROVEMENTS:")
    print("1. [DONE] Removed 'context/document' mentions from prompts")
    print("2. [DONE] Added FAQ filtering for doc3 queries")
    print("3. [DONE] Improved response truncation for vitiligo queries")
    print("\nThe chatbot should now:")
    print("- Give natural responses without mentioning 'context'")
    print("- Exclude FAQs from doc3 unless specifically asked")
    print("- Provide complete responses before adding support links")

if __name__ == "__main__":
    test_improvements()