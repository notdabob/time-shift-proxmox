# VS Code Perplexity Integration Guide

## Installed Extensions

### 1. Perplexity.ai (`ghutu.perplexity-ext`)

- **Purpose**: Direct AI integration for Perplexity.ai with VS Code
- **Features**: Chat, code assistance, research capabilities

### 2. Reprompt (`kwesinavilot.reprompt`)

- **Purpose**: Optimize and enhance prompts using Perplexity Sonar API
- **Features**: Prompt engineering and optimization

### 3. GitMind AI Commit Assistant (`shahabbahreinijangjoo.ai-commit-assistant`)

- **Purpose**: Professional AI commit messages with 13+ AI providers including Perplexity
- **Features**: Automated commit message generation

### 4. Perplexity Theme (`cottonable.perplexity`)

- **Purpose**: VS Code theme using Perplexity AI UI colors
- **Features**: Dark theme matching Perplexity interface

## Setup Instructions

### Perplexity.ai Extension Setup

1. **Set API Key**:

   ```text
<<<<<<< HEAD
   Cmd+Shift+P → "Perplexity: Set API Token" → Enter your Perplexity API key
   ```

2. **Alternative Settings Method**:
   - Open VS Code Settings (`Cmd+,`)
   - Search for "perplexity"
   - Enter API key in extension settings

### Reprompt Extension Setup

1. **Configure Sonar API**:
   - The extension uses Perplexity Sonar API
   - Uses the same API key as main Perplexity extension
   - Access via Command Palette: "Reprompt"

### GitMind Setup

1. **Configure for Perplexity**:
   - Open Command Palette
   - Search for "GitMind"
   - Configure Perplexity as one of the AI providers
<<<<<<< HEAD
   - Use your Perplexity API key.

## Usage Examples

### 1. Code Assistance

- Right-click in code → "Ask Perplexity"
- Highlight code → Command Palette → "Perplexity: Explain Code"

### 2. Research

- Select text → "Perplexity: Research Topic"
- Open Perplexity chat panel for general queries

### 3. Prompt Optimization

- Select a prompt → Command Palette → "Reprompt: Optimize"
- Improve prompt quality for better AI responses

### 4. Smart Commits

- Stage changes → Command Palette → "GitMind: Generate Commit"
- Choose Perplexity as the AI provider

## API Key Reference

Your Perplexity API key is stored in `.env`:

**IMPORTANT SECURITY NOTE:** The key below is an example. Do not commit your actual API keys to version control. The `.env` file should be listed in your `.gitignore` file.

```bash
# sonar-disable-next-line
PERPLEXITY_API_KEY=your_perplexity_api_key_here
```

## Troubleshooting

### Extension Not Working

1. **Check API Key**: Ensure it's correctly set in extension settings
2. **Reload VS Code**: Sometimes extensions need a restart
3. **Check Console**: View → Developer Tools → Console for errors

### API Limits

- Check your Perplexity account usage
- Upgrade plan if needed for higher limits

### Network Issues

- Ensure internet connectivity
- Check firewall settings for VS Code

## Documentation Links

- [Perplexity API Documentation](https://docs.perplexity.ai/)
- [VS Code Extension API](https://code.visualstudio.com/api)

---

_Last Updated: June 30, 2025_
