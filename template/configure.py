#!/usr/bin/env python3
"""
Configure web app template - set app name and framework.

Usage:
    # Set config and sync files:
    uv run configure <app-name> <framework>
    uv run configure my-app streamlit

    # Or edit pyproject.toml [tool.webapp] and sync files:
    uv run configure

    # Force overwrite modified files:
    uv run configure <app-name> <framework> --force
    uv run configure --force

How it works:
  • New files are always copied
  • Unchanged files (identical to template) are updated automatically
  • Modified files (you changed them) are protected unless --force is used

Frameworks: streamlit, dash, fastapi
"""

import hashlib
import re
import shutil
import sys
from pathlib import Path

import tomlkit

# Get repository root (parent of template/ directory)
REPO_ROOT = Path(__file__).parent.parent
PYPROJECT_PATH = REPO_ROOT / "pyproject.toml"
FRAMEWORKS_DIR = Path(__file__).parent / "frameworks"
APP_SRC_DIR = REPO_ROOT / "app_src"


def load_config() -> tuple[str, str]:
    """Load app name and framework from pyproject.toml."""
    with open(PYPROJECT_PATH) as f:
        config = tomlkit.load(f)

    webapp = config.get("tool", {}).get("webapp", {})
    if not webapp:
        print("❌ Error: [tool.webapp] section not found in pyproject.toml")
        sys.exit(1)

    app_name = webapp.get("app_name")
    framework = webapp.get("framework")

    if not app_name or not framework:
        print("❌ Error: [tool.webapp] must have 'name' and 'framework' fields")
        sys.exit(1)

    return app_name, framework


def update_config(app_name: str, framework: str) -> None:
    """Update pyproject.toml [tool.webapp] section preserving comments."""
    with open(PYPROJECT_PATH) as f:
        config = tomlkit.load(f)

    # Ensure [tool.webapp] exists
    if "tool" not in config:
        config["tool"] = {}
    if "webapp" not in config["tool"]:
        config["tool"]["webapp"] = {}

    # Update values
    config["tool"]["webapp"]["app_name"] = app_name
    config["tool"]["webapp"]["framework"] = framework

    # Write back (preserves comments and formatting)
    with open(PYPROJECT_PATH, "w") as f:
        tomlkit.dump(config, f)


def validate_app_name(app_name: str) -> bool:
    """Validate app name contains only safe characters."""
    return bool(re.match(r"^[a-zA-Z0-9_-]+$", app_name))


def files_identical(file1: Path, file2: Path) -> bool:
    """Compare two files using SHA256 hash.

    Args:
        file1: First file path
        file2: Second file path

    Returns:
        True if files have identical content, False otherwise
    """
    if not file1.exists() or not file2.exists():
        return False

    hash1 = hashlib.sha256(file1.read_bytes()).hexdigest()
    hash2 = hashlib.sha256(file2.read_bytes()).hexdigest()

    return hash1 == hash2


def copy_framework_files(framework: str, force: bool = False) -> tuple[list, list, list]:
    """Copy framework files to app_src/ with smart detection.

    Args:
        framework: The framework to copy files from
        force: If True, overwrite modified files without prompting

    Returns:
        Tuple of (copied, updated, protected) file lists
    """
    src = FRAMEWORKS_DIR / framework
    dst = APP_SRC_DIR

    if not src.exists():
        raise ValueError(f"Framework '{framework}' not found in template/frameworks/")

    # Categorize files
    new_files = []       # Files that don't exist in app_src/
    unchanged_files = [] # Files identical to template (safe to update)
    modified_files = []  # Files that differ from template (user changed)

    for file in src.iterdir():
        if file.is_file():
            dest_file = dst / file.name

            if not dest_file.exists():
                new_files.append(file.name)
            elif files_identical(file, dest_file):
                unchanged_files.append(file.name)
            else:
                modified_files.append(file.name)

    # Show summary of what will happen
    print()
    if new_files:
        print(f"📄 New files (will be created):")
        for name in new_files:
            print(f"   + {name}")
        print()

    if unchanged_files:
        print(f"✓ Unchanged files (will be updated):")
        for name in unchanged_files:
            print(f"   ✓ {name}")
        print()

    if modified_files:
        if force:
            print(f"⚠️  Modified files (will be OVERWRITTEN due to --force):")
        else:
            print(f"⚠️  Modified files (will be PROTECTED):")
        for name in modified_files:
            print(f"   ⚠ {name}")
        print()

    # Check if we need to abort due to protected files
    if modified_files and not force:
        print("❌ Cannot proceed: some files have been modified.")
        print("   Your changes will be preserved to prevent data loss.")
        print()
        print("Options:")
        print("  • Use --force to overwrite ALL files (your changes will be lost)")
        print("  • Manually back up your changes and run again")
        print("  • Edit only the new/unchanged files above")
        return [], [], modified_files

    # Perform the copy operations
    copied = []
    updated = []
    protected = []

    for file in src.iterdir():
        if file.is_file():
            dest_file = dst / file.name

            if file.name in new_files:
                # New file - always copy
                shutil.copy2(file, dest_file)
                copied.append(file.name)
            elif file.name in unchanged_files:
                # Unchanged file - safe to update
                shutil.copy2(file, dest_file)
                updated.append(file.name)
            elif file.name in modified_files:
                # Modified file
                if force:
                    # Force mode - overwrite
                    shutil.copy2(file, dest_file)
                    copied.append(file.name)
                else:
                    # Protect user changes
                    protected.append(file.name)

    return copied, updated, protected


def main():
    # Check for --force flag
    force = "--force" in sys.argv
    args = [arg for arg in sys.argv[1:] if arg != "--force"]

    if len(args) == 0:
        # No args: sync mode - read config and update files
        print("📖 Reading config from pyproject.toml [tool.webapp]...")
        app_name, framework = load_config()
        print(f"   app_name: {app_name}")
        print(f"   framework: {framework}")
        print()
        mode = "sync"
    elif len(args) == 2:
        # Two args: set config and sync
        app_name = args[0]
        framework = args[1]

        # Validate inputs
        if not validate_app_name(app_name):
            print(
                "❌ Error: App name must contain only letters, numbers, hyphens, and underscores"
            )
            print(f"   Got: {app_name}")
            sys.exit(1)

        valid_frameworks = ["streamlit", "dash", "fastapi"]
        if framework not in valid_frameworks:
            print(f"❌ Error: Framework must be one of: {', '.join(valid_frameworks)}")
            print(f"   Got: {framework}")
            sys.exit(1)

        mode = "set"
        print(f"🚀 Setting up {framework} app: {app_name}")
        print()
    else:
        print(__doc__)
        sys.exit(1)

    if force:
        print("⚠️  Force mode: existing files will be overwritten")
        print()

    # Update config if in set mode
    if mode == "set":
        print("⚙️  Updating pyproject.toml [tool.webapp]...")
        update_config(app_name, framework)
        print(f"✅ Updated config: name='{app_name}', framework='{framework}'")
        print()

    # Copy framework files (both modes)
    print(f"📦 Analyzing {framework} files in app_src/...")
    try:
        copied, updated, protected = copy_framework_files(framework, force=force)
    except Exception as e:
        print(f"❌ Error copying files: {e}")
        sys.exit(1)

    # Check if operation was blocked
    if protected and not copied and not updated:
        print("💡 To overwrite your modified files, use:")
        print(f"   uv run configure {'--force' if mode == 'sync' else f'{app_name} {framework} --force'}")
        sys.exit(1)

    # Summary message
    print()
    total = len(copied) + len(updated)
    if total > 0:
        operations = []
        if copied:
            operations.append(f"{len(copied)} new")
        if updated:
            operations.append(f"{len(updated)} updated")
        print(f"✅ Success: {', '.join(operations)} file(s)")

    if protected:
        print(f"ℹ️  Protected: {len(protected)} modified file(s) kept (use --force to overwrite)")

    print()
    print("🎉 Setup complete!")
    print()
    print("Next steps:")
    print(f"  1. Review app_src/{framework}_app.py")
    print("  2. Develop using VS Code dev container (recommended):")
    print("     - Open in VS Code")
    print("     - Click 'Reopen in Container'")
    print("  3. OR test with smoke test:")
    print("     uv run smoke_test --wait")
    print("  4. Deploy: cdk deploy")
    print()
    if mode == "sync":
        print(
            "💡 Edit [tool.webapp] in pyproject.toml and run 'uv run configure' to sync!"
        )
    else:
        print("💡 Run 'uv run configure <app-name> <framework>' to switch frameworks!")


if __name__ == "__main__":
    main()
