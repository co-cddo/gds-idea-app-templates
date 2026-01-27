# Application Source Directory

This directory will be populated when you run the configuration script:

```bash
uv run configure <app-name> <framework>
```

## Available Frameworks

- `streamlit` - Streamlit application with Cognito authentication
- `dash` - Dash/Plotly application with Flask backend
- `fastapi` - FastAPI application with app-wide authentication

## Example

```bash
uv run configure my-app streamlit
```

This will copy the framework template files (Dockerfile, pyproject.toml, app code) into this directory, and you can then develop your application here.

## Development

After configuration, you can:

1. **Use VS Code dev container** (recommended):
   - Open in VS Code
   - Click "Reopen in Container"

2. **Test with smoke test**:
   ```bash
   uv run smoke_test --wait
   ```

3. **Deploy to AWS**:
   ```bash
   cdk deploy etc.
   ```
