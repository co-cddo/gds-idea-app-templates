#!/usr/bin/env python3
"""
Configure web app template - set app name and framework.

Usage:
    # Set config and sync files:
    uv run configure <app-name> <framework>
    uv run configure my-app streamlit

    # Or edit pyproject.toml [tool.webapp] and sync files:
    uv run configure

Frameworks: streamlit, dash, fastapi
"""

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


def copy_framework_files(framework: str) -> None:
    """Copy framework files to app_src/."""
    src = FRAMEWORKS_DIR / framework
    dst = APP_SRC_DIR

    if not src.exists():
        raise ValueError(f"Framework '{framework}' not found in template/frameworks/")

    # Copy all files from framework directory
    for file in src.iterdir():
        if file.is_file():
            shutil.copy2(file, dst / file.name)
            print(f"   ✓ {file.name}")


def main():
    if len(sys.argv) == 1:
        # No args: sync mode - read config and update files
        print("📖 Reading config from pyproject.toml [tool.webapp]...")
        app_name, framework = load_config()
        print(f"   app_name: {app_name}")
        print(f"   framework: {framework}")
        print()
        mode = "sync"
    elif len(sys.argv) == 3:
        # Two args: set config and sync
        app_name = sys.argv[1]
        framework = sys.argv[2]

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

    # Update config if in set mode
    if mode == "set":
        print("⚙️  Updating pyproject.toml [tool.webapp]...")
        update_config(app_name, framework)
        print(f"✅ Updated config: name='{app_name}', framework='{framework}'")
        print()

    # Copy framework files (both modes)
    print(f"📦 Copying {framework} files to app_src/...")
    try:
        copy_framework_files(framework)
    except Exception as e:
        print(f"❌ Error copying files: {e}")
        sys.exit(1)
    print(f"✅ Copied {framework} files to app_src/")

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
