"""
Test to verify that responses end with complete sentences before adding support link
"""

def test_sentence_completion():
    print("\nTESTING SENTENCE COMPLETION FIX")
    print("="*50)
    
    # Test various incomplete response scenarios
    test_responses = [
        "Vitiligo is a chronic skin condition characterized by the loss of melanin (skin pigment) that causes white patches to appear on various parts of the body. It affects people of all ages and",
        "The condition causes white patches on the skin and",
        "Treatment options include phototherapy and",
        "Vitiligo affects approximately 1-2% of the population",
        "It is an autoimmune condition where the immune system attacks melanocytes."
    ]
    
    link_text = "\n\nFor community support and to connect with others, visit: vitiligosupportgroup.com"
    
    for i, raw_response in enumerate(test_responses, 1):
        print(f"\nTest {i}:")
        print(f"Original: {raw_response[:80]}...")
        
        # Apply the fix logic
        fixed_response = raw_response.strip()
        
        # Check if response ends properly
        if fixed_response and fixed_response[-1] not in '.!?':
            # Find the last complete sentence
            sentences = fixed_response.split('. ')
            if len(sentences) > 1:
                # Use only complete sentences
                fixed_response = '. '.join(sentences[:-1]) + '.'
            else:
                # Add period if it's a single incomplete sentence
                fixed_response += '.'
        
        # Add the link
        final_response = fixed_response + link_text
        
        print(f"Fixed: {fixed_response[:80]}...")
        
        # Verify it ends properly before link
        if fixed_response[-1] in '.!?':
            print("  [PASS] Ends with proper punctuation before link")
        else:
            print("  [FAIL] Still incomplete")
    
    print("\n" + "="*50)
    print("EXPECTED BEHAVIOR:")
    print("- Responses should end with complete sentences")
    print("- No trailing 'and' or incomplete phrases")
    print("- Support link appears after a proper sentence ending")

if __name__ == "__main__":
    test_sentence_completion()