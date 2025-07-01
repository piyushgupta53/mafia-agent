#!/usr/bin/env python3
"""
Test script to verify environment setup
"""

import os
from dotenv import load_dotenv


def test_env_setup():
    """Test if environment is set up correctly"""

    print("🔍 Testing Environment Setup")
    print("=" * 30)

    # Test .env file loading
    load_dotenv()

    # Check API key
    api_key = os.getenv("DEEPSEEK_API_KEY")

    if not api_key:
        print("❌ DEEPSEEK_API_KEY not found!")
        print("   Please create a .env file with your API key:")
        print("   echo 'DEEPSEEK_API_KEY=your_key_here' > .env")
        return False

    if api_key == "your_deepseek_api_key_here":
        print("❌ API key is still the placeholder value!")
        print("   Please replace 'your_deepseek_api_key_here' with your actual API key")
        return False

    if not api_key.startswith("sk-"):
        print("⚠️  Warning: API key doesn't start with 'sk-'")
        print("   This might not be a valid DeepSeek API key")
        return False

    print("✅ DEEPSEEK_API_KEY found and looks valid")
    print(f"   Key starts with: {api_key[:10]}...")

    # Check .gitignore
    if os.path.exists(".gitignore"):
        with open(".gitignore", "r") as f:
            gitignore_content = f.read()
            if ".env" in gitignore_content:
                print("✅ .env is properly ignored by git")
            else:
                print("⚠️  .env not found in .gitignore")
    else:
        print("⚠️  .gitignore file not found")

    print("\n🎉 Environment setup looks good!")
    print("   You can now run: python run.py")
    return True


if __name__ == "__main__":
    test_env_setup()
