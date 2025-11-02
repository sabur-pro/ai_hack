"""Script to check if the setup is correct."""

import sys
import os


def check_python_version():
    """Check Python version."""
    print("🐍 Checking Python version...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"  Python {version.major}.{version.minor}.{version.micro} - OK")
        return True
    else:
        print(f"   Python {version.major}.{version.minor} - Need Python 3.8+")
        return False


def check_env_file():
    """Check if .env file exists."""
    print("\n⚙️  Checking .env file...")
    if os.path.exists(".env"):
        print("    .env file exists")

        with open(".env", "r") as f:
            content = f.read()
            if "API_GEMINI" in content and "your_" not in content:
                print("    API_GEMINI seems to be configured")
                return True
            else:
                print("     API_GEMINI not configured properly")
                print("    Edit .env and add your Gemini API key")
                return False
    else:
        print("   .env file not found")
        print("  Create .env file with: API_GEMINI=your_key")
        return False


def check_packages():
    """Check if required packages are installed."""
    print("\n📦 Checking packages...")
    required_packages = [
        "fastapi",
        "uvicorn",
        "pydantic",
        "google.generativeai",
        "chromadb",
        "sentence_transformers",
    ]

    all_installed = True
    for package in required_packages:
        try:
            if package == "google.generativeai":
                __import__("google.generativeai")
            else:
                __import__(package)
            print(f"    {package}")
        except ImportError:
            print(f"    {package} - NOT INSTALLED")
            all_installed = False

    if not all_installed:
        print("\n   Run: pip install -r requirements.txt")

    return all_installed


def check_structure():
    """Check project structure."""
    print("\n📁 Checking project structure...")
    required_dirs = [
        "src",
        "src/core",
        "src/infrastructure",
        "src/services",
        "src/api",
        "examples",
        "tests",
    ]

    all_exist = True
    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            print(f"    {dir_path}/")
        else:
            print(f"    {dir_path}/ - MISSING")
            all_exist = False

    return all_exist


def main():
    """Run all checks."""
    print("=" * 60)
    print("🔍 HR AI Agent - Setup Checker")
    print("=" * 60)

    checks = [
        check_python_version(),
        check_env_file(),
        check_packages(),
        check_structure(),
    ]

    print("\n" + "=" * 60)
    if all(checks):
        print(" All checks passed! You're ready to go!")
        print("\n Next steps:")
        print("   1. python examples/simple_usage.py")
        print("   2. python main.py")
        print("   3. Open http://localhost:8000/docs")
    else:
        print(" Some checks failed. Please fix the issues above.")
        print("\n Read QUICKSTART.md or SETUP.md for help")

    print("=" * 60)


if __name__ == "__main__":
    main()

