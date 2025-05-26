# GPT-Commit

A CLI tool that generates commit messages using AI (via CBORG's OpenAI-compatible API) and stages/commits files in Git.

## Features
- **AI-Generated Commit Messages**: Use models like GPT-4.1 to create concise commit messages based on file changes.
- **Model Selection**: Choose from available models (e.g., `openai/gpt-4.1`, `openai/gpt-3.5-turbo`).
- **Interactive Editing**: Edit the generated commit message in your default text editor before committing.
- **Git Integration**: Automatically stages the file and commits with the finalized message.
- **Model Listing**: List available models via `--list-models`.

## Installation
1. **Download the script**:  
   ```bash
    git clone https://git.github.com/aryabhatt/gpt-commit.git
    cd gpt-commit
    ```

2. **Dependencies**:
   ```bash
   pip install openai click gitpython
    ```
3. **Usage**: Obtain an API key and save it in `~/.config/cborg/secrets.json`.
    ```json
    {
        "CBORG_API_KEY": "your_api_key_here",
        "CBORG_BASE_URL": "httsps://api.cborg.lbl.gov"
    }
    ```
3. **Run the script**:
    ```bash
    gpt-commit <file_path> [--model <model_name>] [--list-models]
   ```
    
    - `<file_path>`: Path to the file you want to commit.
    - `--model <model_name>`: Specify the model to use (default is `openai/gpt-4.1`).
    - `--list-models`: List available models.

