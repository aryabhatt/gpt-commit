""" This module provides cli tool to help create log messages for git-commits using GPT models."""
import sys
import json
from pathlib import Path
import click
from git import Repo
import openai

def get_client():
    """    
    Get an OpenAI client instance with API key and base URL from from secrets file.
    Retruns:
        openai.OpenAI: An instance of the OpenAI client.
    """
    secrets_file = Path.home() / ".config/cborg/secrets.json"
    if not secrets_file.is_file():
        print(f"error: can't load API key from {secrets_file.as_posix()}")
        sys.exit(1)

    with open(secrets_file) as f:
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

def generate_commit_message(client, diff_msg, model, new_file_flag=False):
    """
    Generates a commit message based on the provided diff message using the specified model.
    
    Args:
        diff_msg (str): The diff message to be used for generating the commit message.
        model (str): The model to be used for generating the commit message.
    
    Returns:
        str: The generated commit message.
    """
    if new_file_flag:
        msgs = [{
            "role": "user",
            "content": f"Please write a concise commit message that summarizes the newly added file with code:\n{diff_msg}"
        }]
    else:
        msgs = [{
            "role": "user",
            "content": f"Please write a brief commit message for the following diff:\n{diff_msg}"
        }]
    response = client.chat.completions.create(
        model=model,
        messages=msgs,
        temperature=0.0
    )

    if response and response.choices:
        return response.choices[0].message.content.strip()

def stage_and_commit(repo, filename, commit_msg_file):
    """
    Stages the specified file and commits it with the provided commit message.
    
    Args:
        repo (git.Repo): The Git repository instance.
        filename (str): The name of the file to be staged and committed.
        commit_msg_file (file): The file containing the commit message.
    """
    try:
        with open(commit_msg_file.name) as f:
            commit_msg = f.read().strip()
        repo.index.add([filename])
        repo.index.commit(commit_msg)
    except Exception as e:
        print(f"Error during staging or committing: {e}")



@click.command()
@click.argument("filename", required=False)
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

    # If no filename is provided, don't run the rest of the code
    filename = Path(filename) if filename else None
    if not filename or not filename.is_file():
        print("Please provide a valid filename.")
        return

    # Check if this is ideed a git repo
    repo = Repo(Path.cwd())
    if repo.bare:
        print("This is not a git repository")

    # Check if the file is tracked by git
    if filename.as_posix() in repo.untracked_files:
        print(f"file '{filename.as_posix()}' is not tracked by git.")
        return

    # Check if the file has been modified
    diff_list = repo.head.commit.diff(None)
    modified_files = [diff.a_path for diff in diff_list if diff.a_path]
    new_files = [diff.b_path for diff in diff_list if diff.new_file]

    new_file_flag = False
    if filename.as_posix() in new_files:
        with open(filename) as f:
            diff_msg = f.read()
            new_file_flag = True
    elif filename.as_posix() in modified_files:
        diff_msg = repo.git.diff(filename)
    else:
        print(f"{filename.as_posix()} has not been modified.")
        sys.exit(0)

    # ask the model to generate a commit message
    commit_msg = generate_commit_message(client, diff_msg, model, new_file_flag)

    # create a file to edit the commit message
    commit_msg_filename = Path("commit_msg.txt")
    with open(commit_msg_filename, "w") as f:
        f.write(commit_msg)

    # get st_mtime of the file
    commit_msg_file_mtime = commit_msg_filename.stat().st_mtime

    click.edit(filename=commit_msg_filename.as_posix())
    # check if the file has been edited
    if commit_msg_filename.stat().st_mtime == commit_msg_file_mtime:
        print("No changes made to the commit message. Exiting.")
    else:
        # commit the changes
        stage_and_commit(repo, filename, commit_msg_filename)
        # delete the commit message file
    commit_msg_filename.unlink(missing_ok=True)

if __name__ == "__main__":
    gpt_commit()
