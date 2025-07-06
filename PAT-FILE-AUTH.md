# PAT File Authentication Guide

## The Simplest Way to Authenticate

The `.pat` file method is the easiest way to handle GitHub authentication for this private repository.

## Quick Start

1. **Create a `.pat` file with your token:**
   ```bash
   echo 'ghp_YourActualTokenHere' > .pat
   ```

2. **Run any script - it will find your token automatically:**
   ```bash
   ./setup.sh
   # OR
   ./pat-setup.sh
   # OR
   ./time-shift-idrac.sh
   ```

That's it! No password prompts, no complex configuration.

## How It Works

All scripts in this project automatically check for tokens in this order:
1. `.pat` file in current directory
2. `~/.pat` file in home directory
3. `~/.time-shift-proxmox-token` file
4. `GITHUB_TOKEN` environment variable

## Getting a GitHub Token

1. Go to https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Name: `time-shift-proxmox`
4. Select scope: `✓ repo`
5. Click "Generate token"
6. Copy the token (starts with `ghp_`)

## Security Notes

- The `.pat` file is ignored by git (won't be committed)
- Set proper permissions: `chmod 600 .pat`
- You can use comments in the file:
  ```
  # My GitHub Token
  ghp_actualTokenHere
  ```

## Alternative Locations

You can place your `.pat` file in any of these locations:
- `./.pat` (current directory)
- `~/.pat` (home directory)
- `~/.time-shift-proxmox-token` (legacy location)

## Examples

### Using with setup.sh
```bash
echo 'ghp_YourToken' > .pat
wget https://raw.githubusercontent.com/notdabob/time-shift-proxmox/main/setup.sh
sudo bash setup.sh
```

### Using with pat-setup.sh
```bash
# This script will create a .pat template if it doesn't exist
./pat-setup.sh
```

### Environment variable method
```bash
export GITHUB_TOKEN='ghp_YourToken'
./setup.sh
```

## Troubleshooting

If authentication fails:
1. Check your token is valid (not expired)
2. Ensure the token has `repo` scope
3. Verify the token doesn't have extra spaces or newlines
4. Try: `cat .pat | tr -d '\n' > .pat.tmp && mv .pat.tmp .pat`