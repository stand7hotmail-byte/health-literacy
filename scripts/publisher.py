"""File writer and Git operations."""

import os
import subprocess


def save_article(article_dir: str, html: str) -> bool:
    """記事HTMLを保存"""
    try:
        os.makedirs(article_dir, exist_ok=True)
        index_path = os.path.join(article_dir, "index.html")
        with open(index_path, "w", encoding="utf-8") as f:
            f.write(html)
        return True
    except Exception as e:
        print(f"Save error: {e}")
        return False


def git_commit_and_push(message: str) -> bool:
    """Git commit and push"""
    try:
        subprocess.run(["git", "add", "."], check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", message], check=True, capture_output=True)
        subprocess.run(["git", "push"], check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Git error: {e}")
        return False


def git_push() -> bool:
    """Git push only"""
    try:
        subprocess.run(["git", "push"], check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Git push error: {e}")
        return False