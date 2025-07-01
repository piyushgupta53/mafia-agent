#!/usr/bin/env python3
"""
Alternative run script for the Mafia Multi-Agent Game
This is a simplified launcher that you can run directly
"""

import os
import sys
from pathlib import Path


def check_requirements():
    """Check if required packages are installed"""
    required_packages = [
        "autogen",
        "flask",
        "flask_socketio",
        "requests",
        "python-dotenv",
    ]

    missing_packages = []

    for package in required_packages:
        try:
            if package == "python-dotenv":
                __import__("dotenv")
            else:
                __import__(package.replace("-", "_"))
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n📦 Install them with:")
        print(f"   pip install {' '.join(missing_packages)}")
        return False

    return True


def check_environment():
    """Check if environment is properly configured"""
    issues = []

    # Check for DeepSeek API key
    if not os.getenv("DEEPSEEK_API_KEY"):
        issues.append("DEEPSEEK_API_KEY environment variable not set")

    # Check if config file exists
    if not Path("config.py").exists():
        issues.append("config.py file not found")

    if issues:
        print("⚠️  Environment issues found:")
        for issue in issues:
            print(f"   - {issue}")
        print("\n🔧 Setup instructions:")
        print("   1. Set your DeepSeek API key:")
        print("      export DEEPSEEK_API_KEY=your_api_key_here")
        print("   2. Make sure all project files are in the correct structure")
        return False

    return True


def main():
    """Main launcher function"""
    print("🎭 Mafia Multi-Agent Game Launcher")
    print("=" * 50)

    # Check requirements
    if not check_requirements():
        print("\n❌ Please install missing packages and try again")
        sys.exit(1)

    # Check environment
    if not check_environment():
        print("\n❌ Please fix environment issues and try again")
        sys.exit(1)

    print("✅ All checks passed!")
    print("🚀 Starting the game server...")
    print("=" * 50)

    # Import and run the main application
    try:
        from main import main as run_main

        run_main()
    except Exception as e:
        print(f"❌ Error starting the game: {e}")
        print("\n🐛 Debug information:")
        print(f"   Current directory: {os.getcwd()}")
        print(f"   Python path: {sys.path}")
        sys.exit(1)


if __name__ == "__main__":
    main()
