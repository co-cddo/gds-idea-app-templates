#!/bin/bash
# Dev Container Message of the Day
# Shows framework-specific startup instructions

# Read framework from pyproject.toml
if [ -f /workspace-config/pyproject.toml ]; then
    FRAMEWORK=$(grep 'framework = ' /workspace-config/pyproject.toml | head -1 | cut -d'"' -f2)
else
    FRAMEWORK="unknown"
fi

# Define commands based on framework
case "$FRAMEWORK" in
    streamlit)
        APP_FILE="streamlit_app.py"
        START_CMD="uv run streamlit run streamlit_app.py --server.port 80"
        PORT="8501"
        FRAMEWORK_NAME="Streamlit"
        ;;
    dash)
        APP_FILE="dash_app.py"
        START_CMD="uv run python dash_app.py"
        PORT="8501"
        FRAMEWORK_NAME="Dash"
        ;;
    fastapi)
        APP_FILE="fastapi_app.py"
        START_CMD="uv run uvicorn fastapi_app:app --reload --host 0.0.0.0 --port 80"
        PORT="8501"
        FRAMEWORK_NAME="FastAPI"
        ;;
    *)
        APP_FILE="<app_file>"
        START_CMD="<see Dockerfile CMD>"
        PORT="8501"
        FRAMEWORK_NAME="Unknown"
        ;;
esac

# Display welcome message
cat << EOF

╔════════════════════════════════════════════════════════════════╗
║  🚀 Dev Container Ready - ${FRAMEWORK_NAME} App
╠════════════════════════════════════════════════════════════════╣
║  To start the application:
║
║    ${START_CMD}
║
║  Then open: http://localhost:${PORT}
║
║  📝 Your code: /app/${APP_FILE}
║  🔄 Changes auto-reload on save
╚════════════════════════════════════════════════════════════════╝

EOF
