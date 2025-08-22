"""
Test to verify responses end with complete sentences
"""

def test_sentence_completion():
    print("\nTESTING COMPLETE SENTENCE LOGIC")
    print("="*60)
    
    # Simulate responses that might come from the model
    test_cases = [
        {
            "input": "Vitiligo is a skin condition characterized by patches of skin losing their pigment (color). It occurs when the cells that produce melanin, a pigment responsible for skin color, stop working or die. This results in white or depigmented patches on various parts of the body, including the skin and",
            "expected": "Vitiligo is a skin condition characterized by patches of skin losing their pigment (color). It occurs when the cells that produce melanin, a pigment responsible for skin color, stop working or die.",
            "description": "Incomplete 'including the skin and'"
        },
        {
            "input": "The condition affects people of all ages and ethnicities. Treatment options include phototherapy and",
            "expected": "The condition affects people of all ages and ethnicities.",
            "description": "Incomplete 'phototherapy and'"
        },
        {
            "input": "Vitiligo causes white patches on the skin when melanocytes are destroyed or stop",
            "expected": "Vitiligo causes white patches on the skin when melanocytes are destroyed or stop.",
            "description": "Incomplete verb 'stop'"
        },
        {
            "input": "It is an autoimmune condition. The immune system attacks melanocytes.",
            "expected": "It is an autoimmune condition. The immune system attacks melanocytes.",
            "description": "Already complete"
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test['description']}")
        print(f"Input: ...{test['input'][-80:]}")
        
        # Apply the sentence completion logic
        response = test['input'].strip()
        
        # Find complete sentences
        sentences = []
        current_sentence = ""
        
        for char in response:
            current_sentence += char
            if char in '.!?' and len(current_sentence.strip()) > 10:
                sentences.append(current_sentence.strip())
                current_sentence = ""
        
        # Build response from complete sentences only
        if sentences:
            response = " ".join(sentences)
        elif response and response[-1] not in '.!?':
            # No complete sentences, try to salvage
            if '.' in response:
                last_period = response.rfind('.')
                if last_period > 0:
                    response = response[:last_period + 1]
            else:
                response = response.rstrip(',; ') + '.'
        
        print(f"Output: ...{response[-80:]}")
        
        # Check if it ends properly
        if response[-1] in '.!?':
            print("  [PASS] Ends with proper punctuation")
        else:
            print("  [FAIL] Still incomplete")
        
        # Add support link for display
        final = response + "\n\nFor community support and to connect with others, visit: vitiligosupportgroup.com"
        print(f"  With link: Complete sentence + support link")
    
    print("\n" + "="*60)
    print("EXPECTED BEHAVIOR:")
    print("- All responses end with complete sentences")
    print("- Incomplete phrases are removed")
    print("- Support link appears after proper punctuation")

if __name__ == "__main__":
    test_sentence_completion()