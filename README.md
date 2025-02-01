# Conventional Commit Rewriter

A simple Python tool that transforms **raw commit messages** into **Conventional (Semantic) Commit** messages using the new [OpenAI Python API (v1)](https://github.com/openai/openai-python) interface.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Setup](#setup)
- [Usage](#usage)
- [Example](#example)
- [Git Integration (Optional)](#git-integration-optional)
- [Troubleshooting](#troubleshooting)

---

## Overview

This tool leverages the [OpenAI Chat Completion API](https://platform.openai.com/docs/guides/chat) to parse your plain-text commit messages and convert them into the [Conventional Commits](https://www.conventionalcommits.org) format. It helps maintain a **clean**, **consistent**, and **parseable** commit history in your repository.

---

## Features

- **Automatic Classification** into types like `feat`, `fix`, `docs`, etc.
- **Short, Imperative Subject Lines** following the `<type>(<scope>): <subject>` format.
- **Optional** body or `BREAKING CHANGE` footer for major updates.
- **Lightweight** single-file Python script.
- **Uses `python-dotenv`** to keep your **OpenAI API key** out of source control.

---

## Requirements

- **Python 3.8+**
- **Pip** for installing dependencies
- An **OpenAI API Key** ([sign up here](https://platform.openai.com) if you don’t have one)

---

## Installation

1. **Clone** this repository or place the `rewrite_commit_message.py` script in your project.
2. **Install** the required dependencies:
   ```bash
   pip install --upgrade openai
   pip install python-dotenv
   ```

---

## Setup

1. **Create a `.env` file** (in the same folder as `rewrite_commit_message.py`) containing your OpenAI API key:
   ```bash
   OPENAI_API_KEY=sk-1234_your_secret_key
   ```
2. **Ignore** `.env` in your `.gitignore` to avoid committing it:
   ```bash
   echo ".env" >> .gitignore
   ```

---

## Usage

1. **Run the script** with a raw commit message as an argument. The script will output a **Conventional Commit**-formatted message:

   ```bash
   python rewrite_commit_message.py "my raw commit message here"
   ```

2. **Use the output** in an actual `git commit` command:

   ```bash
   git commit -m "$(python rewrite_commit_message.py 'my raw commit message here')"
   ```

---

## Example

```bash
$ python rewrite_commit_message.py "added a new pipeline validator and simulator"
feat(pipeline): add validator and simulator
```

**Example raw input**:
```
"fixing the user login bug that caused random timeouts"
```
**Example output**:
```
fix(auth): resolve user login timeout issue
```

---

## Git Integration (Optional)

Want to fully automate this process? You can integrate the script into a **Git hook** so every commit message is auto-converted. For example, a simple `commit-msg` hook:

1. Copy the `commit-msg` file into your `.git/hooks/` (must be executable).
2. Replace the `PATH/TO/YOUR/rewrite_commit_message.py` with the actual path to `rewrite_commit_message.py`
3. Now, whenever you run `git commit -m "some random message"`, the hook calls OpenAI to rewrite it automatically.

> **Note**: This approach will invoke the OpenAI API on every commit, which could incur usage costs. Consider setting usage limits in your [OpenAI dashboard](https://platform.openai.com/account/usage).

---

## Troubleshooting

1. **`OPENAI_API_KEY not set`**  
   - Ensure `.env` is in the same directory and contains a valid `OPENAI_API_KEY`.  
   - Make sure you’re calling `load_dotenv()` **before** accessing `os.getenv(...)`.
2. **Version Mismatch**  
   - Double-check you installed `openai>=1.0.0`.  
   - Run `pip show openai` to confirm the version is correct.  
3. **Multiple Python Environments**  
   - Ensure you’re installing dependencies in the same environment you’re running the script from.
4. **Billing / Usage**  
   - The script uses the [OpenAI API](https://platform.openai.com/) on each invocation, so check your usage dashboard regularly.
```