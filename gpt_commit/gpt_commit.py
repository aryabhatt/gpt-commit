"""
Command line tool to commit changes to a file using AI-generated commit messages.
"""
import os
import json
import tempfile
from pathlib import Path
import click
from git import Repo
import openai

class GitCommitHelper:
    """
    Helper class to manage Git operations and OpenAI interactions.
    """

    def __init__(self, api_key=None, base_url=None, secrets_file=None):
        """
        Initialize the helper by setting up the OpenAI client and Git repo.
        """
        self.api_key = api_key
        self.base_url = base_url
        self.secrets_file = secrets_file or (Path.home() / ".config/cborg/secrets.json")
        self.client = self._get_client()
        self.repo = self._get_repo()

    def _get_client(self):
        """
        Create an OpenAI client using secrets file or environment variables.
        """
        if not self.api_key or not self.base_url:
            if self.secrets_file.exists():
                with open(self.secrets_file, encoding='utf-8') as f:
                    secrets = json.load(f)
                self.api_key = secrets.get("CBORG_API_KEY") or os.getenv("CBORG_API_KEY")
                self.base_url = secrets.get("CBORG_BASE_URL") or os.getenv("CBORG_BASE_URL")
            else:
                self.api_key = os.getenv("CBORG_API_KEY")
                self.base_url = os.getenv("CBORG_BASE_URL")

        if not self.api_key or not self.base_url:
            raise RuntimeError("Missing API credentials for OpenAI/CBORG.")

        return openai.OpenAI(api_key=self.api_key, base_url=self.base_url)

    def _get_repo(self):
        """
        Get the current working directory's Git repository.
        """
        repo = Repo(Path.cwd())
        if repo.bare:
            raise RuntimeError("Not a valid Git repository.")
        return repo

    def get_models(self):
        """
        Fetch available models from OpenAI client.
        """
        try:
            models = self.client.models.list()
            return [m.id for m in models.data]
        except (openai.OpenAIError, ConnectionError, TimeoutError) as e:
            print(f"Error fetching models: {e}")
            return []

    def generate_commit_message(self, diff_msg, model):
        """
        Generate commit message from diff using a language model.
        """
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[{
                    "role": "user",
                    "content": f"Please write a brief commit message \
                         for the following diff:\n{diff_msg}"
                }],
                temperature=0.0
            )
            if response and response.choices:
                return response.choices[0].message.content.strip()
        except (openai.OpenAIError, ConnectionError, TimeoutError) as e:
            print(f"Error generating commit message: {e}")
        return None

    def get_diff(self, filename):
        """
        Get the diff for the given filename (unstaged or staged).
        """
        if filename not in self.repo.git.ls_files().splitlines():
            raise FileNotFoundError(f"'{filename}' is not tracked by git.")

        diff_msg = self.repo.git.diff(filename) or self.repo.git.diff('HEAD', filename)
        return diff_msg

    def stage_and_commit(self, filename, commit_message):
        """
        Stage file and commit with provided message.
        """
        try:
            self.repo.git.add(filename)
            self.repo.index.commit(commit_message)
            print(f"Committed '{filename}' with message: {commit_message}")
        except (OSError, ValueError) as e:
            print(f"Error during commit: {e}")

    def commit_file_with_ai(self, filename, model="openai/gpt-4.1", edit=True, dry_run=False):
        """
        Main workflow: get diff, generate commit message, optionally edit, commit.
        """
        diff_msg = self.get_diff(filename)
        if not diff_msg:
            print(f"No changes detected for '{filename}'.")
            return

        commit_msg = self.generate_commit_message(diff_msg, model)
        if not commit_msg:
            print("Failed to generate commit message.")
            return

        print(f"Generated commit message:\n{commit_msg}")

        if dry_run:
            return

        if edit:
            with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_file:
                temp_file.write(commit_msg)
                temp_path = Path(temp_file.name)

            click.edit(filename=str(temp_path))
            commit_msg = temp_path.read_text(encoding='utf-8').strip()
            if not commit_msg:
                print("Commit message empty after editing. Aborting.")
                return

        self.stage_and_commit(filename, commit_msg)


@click.command()
@click.argument("filename", type=click.Path(exists=True))
@click.option("--model", default="openai/gpt-4.1", help="Model to use")
@click.option("--list-models", is_flag=True)
@click.option("--dry-run", is_flag=True)
@click.option("--no-edit", is_flag=False, help="No interactive mode")
def gpt_commit(filename, model, list_models, dry_run, no_edit):
    """
    Commit changes to a file using AI-generated commit messages.
    Arguments:
        FILENAME: Path to the file to commit.
    Options:
        --model: Specify the language model to use.
        --list-models: List available models and exit.
        --dry-run: Show the generated commit message without committing.
        --no-edit: Skip interactive editing of the commit message.
    """
    helper = GitCommitHelper()

    if list_models:
        for m in helper.get_models():
            print(f"- {m}")
        return

    helper.commit_file_with_ai(filename, model=model, edit=not no_edit, dry_run=dry_run)
