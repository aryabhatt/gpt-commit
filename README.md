# GPT-Commit

[⬇️ Download `gpt_commit.py`](https://github.com/aryabhatt/gpt-commit/raw/main/gpt_commit.py)

A CLI tool that generates commit messages using AI (via CBORG's OpenAI-compatible API) and stages/commits files in Git.

## Features
- **AI-Generated Commit Messages**: Use models like GPT-4.1 to create concise commit messages based on file changes.
- **Model Selection**: Choose from available models (e.g., `openai/gpt-4.1`, `openai/gpt-3.5-turbo`).
- **Interactive Editing**: Edit the generated commit message in your default text editor before committing.
- **Git Integration**: Automatically stages the file and commits with the finalized message.
- **Model Listing**: List available models via `--list-models`.

## Installation
1. **Download the script**:  
   [⬇️ Download `gpt_commit.py`](https://github.com/aryabhatt/gpt-commit/raw/main/gpt_commit.py)

2. **Dependencies**:
   ```bash
   pip install openai click gitpython

## Usage
    **Get and API Key and save it in `~/.config/gpt_commit/config.json`**:
    ```json
    {
        "CBORG_API_KEY": "your_api_key_here",
        "CBORG_BASE_URL": "httsps://api.cborg.gov"
    }
