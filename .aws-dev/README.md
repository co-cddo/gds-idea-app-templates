# AWS Dev Container Credentials

This directory contains temporary AWS credentials for the dev container.

## How it works

1. **On your host machine**, run: `uv run provide_role`
2. Enter your MFA code when prompted
3. Credentials are written to `credentials` and `config` files in this directory
4. These files are automatically mounted into the dev container at `/home/vscode/.aws/`
5. The AWS SDK/CLI in the container uses these credentials automatically

## Files

- `credentials` - AWS temporary credentials (access key, secret key, session token)
- `config` - AWS configuration (region, output format)

Both files are auto-generated and should not be edited manually.

## Security

- ✅ This entire directory is gitignored
- ✅ Credentials are temporary (expire after 8 hours by default)
- ✅ Mounted read-only into the container
- ✅ Only exists on your local machine

## Refreshing credentials

When credentials expire, simply re-run: `uv run provide_role`

The container will see the updated credentials immediately (no restart needed).
