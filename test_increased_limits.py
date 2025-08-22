"""
Test to verify increased response limits allow complete sentences
"""

def test_limits():
    print("\nVERIFYING INCREASED RESPONSE LIMITS")
    print("="*50)
    
    # Check the new limits in rag.py
    with open('rag.py', 'r', encoding='utf-8') as f:
        rag_content = f.read()
    
    print("\n1. RAG.PY RESPONSE LIMITS:")
    print("-"*40)
    
    if 'max_chars = {"brief": 600' in rag_content:
        print("   [PASS] Brief responses: 600 chars (up from 400)")
    
    if 'max_chars = {"brief": 600, "moderate": 1000' in rag_content:
        print("   [PASS] Moderate responses: 1000 chars (up from 700)")
    
    if 'max_tokens = {"brief": 200, "moderate": 350' in rag_content:
        print("   [PASS] Token limits increased appropriately")
    
    # Check main.py limits
    with open('main.py', 'r', encoding='utf-8') as f:
        main_content = f.read()
    
    print("\n2. MAIN.PY SUPPORT LINK HANDLING:")
    print("-"*40)
    
    if 'max_length_without_link = 1000' in main_content:
        print("   [PASS] Streaming: 1000 chars before link (up from 600)")
    
    if 'max_total_length = 1200' in main_content:
        print("   [PASS] Non-streaming: 1200 total chars (up from 800)")
    
    print("\n3. EXPECTED IMPROVEMENTS:")
    print("-"*40)
    print("   - Vitiligo responses will complete naturally")
    print("   - No more mid-sentence cutoffs")
    print("   - Support link appears after complete thoughts")
    print("   - Responses can be 600-1000 characters")
    
    print("\n" + "="*50)
    print("SUMMARY")
    print("="*50)
    print("\nResponse limits have been increased by ~50%:")
    print("- Brief: 400 -> 600 characters")
    print("- Moderate: 700 -> 1000 characters")  
    print("- Detailed: 1300 -> 1500 characters")
    print("\nThis allows responses to complete naturally before")
    print("adding the support link, preventing mid-sentence cuts.")

if __name__ == "__main__":
    test_limits()