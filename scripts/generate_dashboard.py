import requests
import os

ORG = "oe-alliance-plugins"
TOKEN = os.environ.get("GITHUB_TOKEN")
HEADERS = {"Authorization": f"token {TOKEN}"}


def get_repos():
    url = f"https://api.github.com/orgs/{ORG}/repos?per_page=100"
    repos = []
    while url:
        resp = requests.get(url, headers=HEADERS).json()
        repos.extend(resp)
        url = resp.links.get('next', {}).get('url')
    return repos


def get_last_workflows(repo_name):
    url = f"https://api.github.com/repos/{ORG}/{repo_name}/actions/runs?per_page=50"
    resp = requests.get(url, headers=HEADERS).json()
    workflows = resp.get("workflow_runs", [])
    ruff_status = "-"
    lint_status = "-"
    last_update = "-"

    for run in workflows:
        name = run['name'].lower()
        if "ruff" in name:
            ruff_status = "✅" if run['conclusion'] == "success" else "❌"
        if "pylint" in name:
            lint_status = "✅" if run['conclusion'] == "success" else "❌"
    if workflows:
        last_update = workflows[0]['updated_at']
    return ruff_status, lint_status, last_update


def generate_markdown(repos):
    lines = [
        "# Org Dashboard\n",
        "| Repo | Ruff | Lint | Last Update |",
        "| --- | --- | --- | --- |"
    ]
    for repo in repos:
        name = repo['name']
        ruff, lint, updated = get_last_workflows(name)
        lines.append(f"| {name} | {ruff} | {lint} | {updated} |")
    return "\n".join(lines)


def main():
    repos = get_repos()
    md = generate_markdown(repos)
    with open("README.md", "w") as f:
        f.write(md)


if __name__ == "__main__":
    main()
