#!/usr/bin/env python3
import sys
import os
import re
import subprocess

from dotenv import load_dotenv
from openai import OpenAI, APIError

def get_recent_scopes(max_commits=20):
    """
    Retrieve the last `max_commits` commit subjects and
    parse them for known scopes in format:
      <type>(<scope>): <subject>
    Returns a set of unique scopes.
    """
    scopes = set()
    try:
        # Run Git to get the last n commit messages
        recent_commits = subprocess.check_output(
            ["git", "log", f"-n{max_commits}", "--pretty=format:%s"],
            text=True
        ).splitlines()
    except subprocess.CalledProcessError:
        return scopes  # If this fails (e.g. not in a git repo), return empty set

    # Simple Regex for Conventional Commits: type(scope):
    pattern = re.compile(r"^[a-zA-Z]+(?:\(([^\)]+)\))?:")
    for commit in recent_commits:
        match = pattern.match(commit)
        if match:
            scope = match.group(1)
            if scope:
                scopes.add(scope.strip())
    return scopes

def get_staged_files():
    """Return a list of filenames that are staged for commit."""
    try:
        output = subprocess.check_output(["git", "diff", "--cached", "--name-only"], text=True)
        return [line.strip() for line in output.splitlines() if line.strip()]
    except subprocess.CalledProcessError:
        return []

def get_staged_diff():
    try:
        return subprocess.check_output(["git", "diff", "--cached"], text=True)
    except subprocess.CalledProcessError:
        return ""

def detect_breaking_change(diff_text):
    """
    Return True if local heuristics suspect a BREAKING CHANGE.
    We'll confirm with the user before finalizing.
    """

    removed_lines = []
    for line in diff_text.splitlines():
        if line.startswith("-"):
            removed_lines.append(line[1:].strip())

    public_patterns = [
        re.compile(r"\bpublic\b"),
        re.compile(r"\bexport\b"),
        re.compile(r"\bfunction\s+[A-Za-z0-9_]+\s*\("),
        re.compile(r"\bclass\s+[A-Z]"),
        re.compile(r"^func\s+[A-Z][a-zA-Z0-9_]*\s*\("),
        re.compile(r"^func\s*\([^)]*\)\s+[A-Z][a-zA-Z0-9_]*\s*\("),
        re.compile(r"^type\s+[A-Z][a-zA-Z0-9_]*\s+(struct|interface)"),
    ]
    for rline in removed_lines:
        for pat in public_patterns:
            if pat.search(rline):
                return True

    return False

def main():
    # 1. Load environment variables from .env
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY is not set.")
        sys.exit(1)

    # 2. Capture the raw commit message from CLI arguments
    if len(sys.argv) < 2:
        print("Usage: python rewrite_commit_message.py <commit-message>")
        sys.exit(1)

    raw_message = " ".join(sys.argv[1:])

    # 3. Retrieve the set of known scopes from recent commits
    known_scopes = get_recent_scopes(max_commits=1000)
    scopes_list = ", ".join(sorted(known_scopes)) if known_scopes else "none"

    # 4. Gather local diff & detect potential break
    diff_text = get_staged_diff()
    if not diff_text.strip():
        suspected_breaking = "false"
    else:
        suspected_breaking = detect_breaking_change(diff_text)

    # 5. Gather staged files
    staged_files = "\n".join(get_staged_files())

    # 6. Prepare a system prompt that instructs the model
    system_prompt = f"""\
You are an assistant that converts any given commit message into a Conventional Commit message.
Follow these rules:
1. Use one of the standard types: feat, fix, docs, chore, refactor, style, test, build, ci, perf.
2. If the commit references or includes "BREAKING CHANGE" or a major incompatible change, append a '!' after the type or scope, e.g. feat!: or feat(ui)!:
3. The subject must be short, imperative style, describing what the commit does.
4. If there's a breaking change, ensure there's a footer line "BREAKING CHANGE: <description>" after the body.
5. Known scopes in this repo are: {scopes_list}. If the new commit matches one of these areas, reuse the same scope. If uncertain, guess or omit the scope.
6. Output only the final commit message with no extra commentary.

Based on local detection, suspected_breaking={suspected_breaking}.

Changed files:
{staged_files}
"""

    # 7. Instantiate the OpenAI client
    client = OpenAI(api_key=api_key)

    try:
        # 8. Send the request to the Chat Completions endpoint
        response = client.chat.completions.create(
            model="gpt-4o",  # from docs, or use e.g. "gpt-4" or "gpt-3.5-turbo" if supported
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": raw_message}
            ],
            temperature=0.2,
        )
        # 9. Extract the AI-generated commit message
        semantic_commit = response.choices[0].message.content.strip()

        # 10. remove ``` from the response
        semantic_commit = semantic_commit.replace("```\n", "")
        semantic_commit = semantic_commit.replace("\n```", "")

        print(semantic_commit)

    except APIError as e:
        print("Error calling OpenAI API:", e)
        sys.exit(1)

if __name__ == "__main__":
    main()
