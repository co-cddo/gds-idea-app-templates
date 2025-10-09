#!/bin/bash
set -e

echo "🚀 Framework Setup Script"
echo "=========================="
echo ""

# Parse arguments or prompt interactively
FRAMEWORK=""
APP_NAME=""

if [ $# -eq 0 ]; then
  # Interactive mode
  echo "Available frameworks:"
  echo "  1) streamlit"
  echo "  2) dash"
  echo ""
  read -p "Choose a framework (1-2): " choice

  case $choice in
    1) FRAMEWORK="streamlit" ;;
    2) FRAMEWORK="dash" ;;
    *)
      echo "❌ Invalid choice. Exiting."
      exit 1
      ;;
  esac

  echo ""
  read -p "Enter app name (leave empty to keep current): " APP_NAME

elif [ $# -eq 1 ]; then
  # Framework only
  FRAMEWORK="$1"

elif [ $# -eq 2 ]; then
  # Framework and app name
  FRAMEWORK="$1"
  APP_NAME="$2"

else
  echo "Usage: $0 [framework] [app-name]"
  echo "  framework: streamlit, dash"
  echo "  app-name: optional, name for your application"
  exit 1
fi

# Validate framework
if [ ! -d "frameworks/$FRAMEWORK" ]; then
  echo "❌ Framework '$FRAMEWORK' not found in frameworks/ directory"
  exit 1
fi

echo ""
echo "📦 Switching to $FRAMEWORK framework..."

# Copy framework files to app_src/
cp "frameworks/$FRAMEWORK/Dockerfile" app_src/
cp "frameworks/$FRAMEWORK/pyproject.toml" app_src/
cp frameworks/$FRAMEWORK/*.py app_src/ 2>/dev/null || true

echo "✅ Copied $FRAMEWORK files to app_src/"

# Update app name in app.py if provided
if [ -n "$APP_NAME" ]; then
  if [[ ! $APP_NAME =~ ^[a-zA-Z0-9_-]+$ ]]; then
    echo "❌ App name must contain only letters, numbers, hyphens, and underscores."
    exit 1
  fi

  # Update APP_NAME in app.py
  if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' "s/APP_NAME = \".*\"/APP_NAME = \"${APP_NAME}\"/" app.py
  else
    # Linux
    sed -i "s/APP_NAME = \".*\"/APP_NAME = \"${APP_NAME}\"/" app.py
  fi

  # Update name in pyproject.toml
  if [[ "$OSTYPE" == "darwin"* ]]; then
    sed -i '' "s/name = \".*\"/name = \"${APP_NAME}\"/" app_src/pyproject.toml
  else
    sed -i "s/name = \".*\"/name = \"${APP_NAME}\"/" app_src/pyproject.toml
  fi

  echo "✅ Updated app name to '$APP_NAME'"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Update health_check_path in app.py if needed:"
case $FRAMEWORK in
  streamlit)
    echo "     health_check_path=\"/_stcore/health\""
    ;;
  dash)
    echo "     health_check_path=\"/health\""
    ;;
esac
echo "  2. Run locally:"
case $FRAMEWORK in
  streamlit)
    echo "     cd app_src && uv run streamlit run streamlit_app.py"
    ;;
  dash)
    echo "     cd app_src && uv run gunicorn dash_app:server"
    ;;
esac
echo "  3. Test with: ./smoke-test.sh"
echo "  4. Deploy with: cdk deploy"
echo ""
echo "💡 You can switch frameworks anytime by running this script again!"
