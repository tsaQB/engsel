import subprocess
import requests
import xml.etree.ElementTree as ET

DEFAULT_OWNER = "tsaQB"
DEFAULT_REPO  = "engsel"
BRANCH        = "main"

def get_repo_owner_and_name():
    """Detect repo owner and name from git remote origin URL, fallback to default."""
    try:
        remote_url = subprocess.check_output(
            ["git", "config", "--get", "remote.origin.url"],
            stderr=subprocess.DEVNULL
        ).decode().strip()
        if "github.com" in remote_url:
            clean = remote_url.split("github.com")[-1].lstrip("/:").removesuffix(".git")
            parts = clean.split("/")
            if len(parts) == 2:
                return parts[0], parts[1]
    except Exception:
        pass
    return DEFAULT_OWNER, DEFAULT_REPO

def get_local_commit():
    """Return current local commit hash, or None if not in a git repo."""
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL
        ).decode().strip()
    except Exception:
        return None

def is_ancestor(commit_sha):
    """Check if commit_sha is already an ancestor of HEAD (i.e. already applied locally)."""
    try:
        res = subprocess.run(
            ["git", "merge-base", "--is-ancestor", commit_sha, "HEAD"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return res.returncode == 0
    except Exception:
        return False

def get_latest_commit_atom():
    """Return the latest commit SHA from GitHub via the Atom feed (no auth)."""
    owner, repo = get_repo_owner_and_name()
    url = f"https://github.com/{owner}/{repo}/commits/{BRANCH}.atom"
    r = requests.get(url, timeout=5)
    r.raise_for_status()
    root = ET.fromstring(r.text)
    ns = {"a": "http://www.w3.org/2005/Atom"}
    entry = root.find("a:entry", ns)
    if entry is None:
        return None
    entry_id = entry.find("a:id", ns)
    if entry_id is None or not entry_id.text:
        return None
    # The SHA is the last path segment of the <id> URL
    return entry_id.text.rsplit("/", 1)[-1]

def check_for_updates():
    local = get_local_commit()
    try:
        remote = get_latest_commit_atom()
    except Exception:
        remote = None

    if not remote:
        # Could not fetch remote commit
        return False

    if not local:
        # Not a git repo
        return False

    if local == remote or is_ancestor(remote):
        # Up to date (or local is ahead of remote feed)
        return False

    print(f"⚠️  A newer version is available (remote {remote[:7]} vs local {local[:7]}).")
    print("   Run: git pull --rebase to update.")
    return True
