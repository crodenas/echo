#!/usr/bin/env python3
"""Verification script for Echo project structure.

Run this script to verify that the project restructuring was successful.
"""

import sys
from pathlib import Path


def check_file_exists(path: Path, description: str) -> bool:
    """Check if a file exists and print result."""
    exists = path.exists()
    status = "✅" if exists else "❌"
    print(f"{status} {description}: {path}")
    return exists


def check_directory_exists(path: Path, description: str) -> bool:
    """Check if a directory exists and print result."""
    exists = path.is_dir()
    status = "✅" if exists else "❌"
    print(f"{status} {description}: {path}")
    return exists


def main():
    """Run all verification checks."""
    print("=" * 70)
    print("Echo Project Structure Verification")
    print("=" * 70)

    project_root = Path(__file__).parent.parent  # Go up from scripts/ to project root
    all_checks_passed = True

    # Check directories
    print("\n📁 Checking Directory Structure...")
    dirs = [
        (project_root / "src" / "services", "Services layer"),
        (project_root / "tests", "Tests directory"),
        (project_root / "examples", "Examples directory"),
        (project_root / "examples" / "data", "Sample data directory"),
        (project_root / "scripts", "Scripts directory"),
        (project_root / "src" / "templates", "Templates directory"),
        (project_root / "docs", "Documentation directory"),
    ]

    for path, desc in dirs:
        if not check_directory_exists(path, desc):
            all_checks_passed = False

    # Check key files
    print("\n📄 Checking Key Files...")
    files = [
        (project_root / "src" / "services" / "campaign_service.py", "Campaign service"),
        (project_root / "src" / "services" / "__init__.py", "Services __init__"),
        (project_root / "tests" / "conftest.py", "Test configuration"),
        (project_root / "tests" / "test_api.py", "API tests"),
        (project_root / "tests" / "test_campaign_service.py", "Service tests"),
        (project_root / "docs" / "project_structure.md", "Architecture docs"),
        (project_root / "docs" / "MIGRATION.md", "Migration guide"),
        (project_root / "QUICK_REFERENCE.md", "Quick reference"),
        (project_root / "RESTRUCTURE_SUMMARY.md", "Restructure summary"),
    ]

    for path, desc in files:
        if not check_file_exists(path, desc):
            all_checks_passed = False

    # Check deprecated/removed
    print("\n🗑️  Checking Removed Items...")
    removed = [
        (project_root / "templates", "Root templates directory (should be removed)"),
    ]

    for path, desc in removed:
        exists = path.exists()
        status = "❌" if exists else "✅"
        print(f"{status} {desc}: {'STILL EXISTS' if exists else 'removed'}")
        if exists:
            all_checks_passed = False

    # Check that data moved to examples (except .db files)
    src_data_dir = project_root / "src" / "data"
    if src_data_dir.exists():
        json_files = list(src_data_dir.glob("*.json"))
        if json_files:
            print(
                f"❌ src/data/ still contains data files: {[f.name for f in json_files]}"
            )
            all_checks_passed = False
        else:
            print("✅ src/data/ only contains database files (OK)")

    # Check imports
    print("\n🔍 Checking Python Imports...")
    try:
        sys.path.insert(0, str(project_root / "src"))

        # Test service import
        from services import campaign_service

        print("✅ Services layer imports successfully")

        # Test models import
        from core.models import Campaign

        print("✅ Core models import successfully")

        # Test main app import
        from main import app

        print("✅ FastAPI app imports successfully")

    except ImportError as e:
        print(f"❌ Import error: {e}")
        all_checks_passed = False

    # Summary
    print("\n" + "=" * 70)
    if all_checks_passed:
        print("✅ All checks passed! Project structure is correct.")
        print("\n📚 Next steps:")
        print("  - Read QUICK_REFERENCE.md for quick start guide")
        print("  - Read docs/project_structure.md for architecture details")
        print("  - Run: uv run fastapi dev src/main.py")
        print("  - Run: uv run pytest")
        return 0
    else:
        print("❌ Some checks failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
