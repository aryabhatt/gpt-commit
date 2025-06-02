
import openai # CBORG API Proxy Server is OpenAI-compatible through the openai module
import json
import click
from git import Repo
from pathlib import Path

def get_client():
    """    
    Get an OpenAI client instance with API key and base URL from from secrets file.
    Retruns:
        openai.OpenAI: An instance of the OpenAI client.
    """
    secrets_file = Path.home() / ".config/cborg/secrets.json"
    if not secrets_file.is_file():
        print(f"error: can't load API key from {secrets_file.as_posix()}")
        exit(1)

    with open(secrets_file, "r") as f:
        secrets = json.load(f)
        api_key = secrets['CBORG_API_KEY']
        base_url = secrets['CBORG_BASE_URL']
    return openai.OpenAI(api_key=api_key, base_url=base_url)

def get_models(client):
    """
    Fetches the list of available models from the OpenAI client.
    Args:
        client (openai.OpenAI): An instance of the OpenAI client.
    Returns:
        list: A list of model IDs.
    """
    try:
        models = client.models.list()
        return [model.id for model in models.data]
    except Exception as e:
        print(f"Error fetching models: {e}")
        return []
    
def generate_commit_message(client, diff_msg, model):
    """
    Generates a commit message based on the provided diff message using the specified model.
    
    Args:
        diff_msg (str): The diff message to be used for generating the commit message.
        model (str): The model to be used for generating the commit message.
    
    Returns:
        str: The generated commit message.
    """
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user", 
                "content": f"Please write a brief commit message for the following diff:\n{diff_msg}"
            }
        ],
        temperature=0.0  
    )
    
    if response and response.choices:
        return response.choices[0].message.content.strip()
    else:
        return None

def stage_and_commit(repo, filename, commit_msg_file):
    """
    Stages the specified file and commits it with the provided commit message.
    
    Args:
        repo (git.Repo): The Git repository instance.
        filename (str): The name of the file to be staged and committed.
        commit_msg_file (file): The file containing the commit message.
    """
    try:
        repo.git.add(filename)
        with open(commit_msg_file.name, "r") as f:
            commit_msg = f.read().strip()
        repo.index.commit(commit_msg)
    except Exception as e:
        print(f"Error during staging or committing: {e}")



@click.command()
@click.argument("filename", type=click.Path(exists=True), required=False)
@click.option("--list-models", is_flag=True, help="List available models")
@click.option("--model", default="openai/gpt-4.1", help="Model to use")
def gpt_commit(filename, model, list_models):
    """Generate a commit message using a language model for the given file.
    \n\n    Example usage:
    \n    gpt-commit <filename>
    \n    gpt-commit <filename> --model openai/gpt-4.1
    \n    gpt-commit --list-models
    """

    # get an instance of client
    client = get_client()

    # get a list of modles
    models = get_models(client)

    # If --list-models is specified, print the available models and exit
    if list_models:
        for m in models:
            print(f"- {m}")
        return

    # Check if model is valid
    if model not in models:
        print(f"Model '{model}' is not available. Please choose from the following models:")
        for m in models:
            print(f"- {m}")
        return



    # Check if this is ideed a git repo
    cwd = Path.cwd()
    repo = Repo(cwd)
    if repo.bare:
        print("This is not a git repository")

    # Get the dff from the last commit
    diff_msg = repo.git.diff(filename)

    commit_msg = generate_commit_message(client, diff_msg, model)
    print(commit_msg)    
    # create a file to edit the commit message
    with open("commit_msg.txt", "w") as commit_msg_file:
        commit_msg_file.write(commit_msg)
    #click.edit(filename=commit_msg_file.name)

    # commmt the file with the commit message 
    #stage_and_commit(repo, filename, commit_msg_file)

if __name__ == "__main__":
    gpt_commit() 
