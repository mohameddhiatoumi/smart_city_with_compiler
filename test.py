# test_openrouter.py
import os
from ai_module import AIGenerator

# Check if API key is set
api_key = os.getenv("OPENROUTER_API_KEY")
print(f"✓ API Key found: {api_key is not None}")

if api_key:
    print(f"  Key starts with: {api_key[:15]}...")
    
    # Test OpenRouter
    try:
        ai = AIGenerator(db_path="neo_sousse.db", use_openrouter=True)
        print(f"\n✓ AI Generator initialized!")
        print(f"  Provider: OpenRouter")
        print(f"  Model: {ai.model}")
        print("\n🎉 OpenRouter is working!")
    except Exception as e:
        print(f"\n✗ Error: {e}")
else:
    print("\n✗ No API key found!")
    print("Set it with: set OPENROUTER_API_KEY=your-key")