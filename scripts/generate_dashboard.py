import requests
import os

ORG = "oe-alliance-plugins"
TOKEN = os.environ.get("ORG_PAT")
HEADERS = {"Authorization": f"token {TOKEN}"}


def get_repos():
    """Alle Repos der Org abrufen, außer .github"""
    url = f"https://api.github.com/orgs/{ORG}/repos?per_page=100"
    repos = []
    while url:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        resp_json = response.json()
        for repo in resp_json:
            if repo['name'] != ".github":  # Ignorieren
                repos.append(repo)
        url = response.links.get('next', {}).get('url')
    return repos


def get_last_workflows(repo_name):
    """Letzten Ruff- und Lint-Workflow abrufen"""
    url = f"https://api.github.com/repos/{ORG}/{repo_name}/actions/runs?per_page=50"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    workflows = response.json().get("workflow_runs", [])

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


def sort_repos_by_status(repo_list):
    """Sortiert: zuerst Repos mit Fehlern, dann ✅"""
    def sort_key(item):
        # ❌ → 0, ✅ → 1, '-' → 2
        def val(status):
            if status == "❌":
                return 0
            if status == "✅":
                return 1
            return 2
        ruff, lint = item['ruff'], item['lint']
        return (min(val(ruff), val(lint)), item['name'].lower())

    return sorted(repo_list, key=sort_key)


def generate_markdown(repos):
    """Markdown-Tabelle erstellen"""
    repo_data = []
    for repo in repos:
        name = repo['name']
        ruff, lint, updated = get_last_workflows(name)
        repo_data.append({
            "name": name,
            "ruff": ruff,
            "lint": lint,
            "updated": updated
        })

    # Sortieren
    sorted_repos = sort_repos_by_status(repo_data)

    lines = [
        "# Org Dashboard\n",
        "| Repo | Ruff | Lint | Last Update |",
        "| --- | --- | --- | --- |"
    ]
    for repo in sorted_repos:
        lines.append(f"| {repo['name']} | {repo['ruff']} | {repo['lint']} | {repo['updated']} |")
    return "\n".join(lines)


def main():
    print("Fetching repos...")
    repos = get_repos()
    print(f"Found {len(repos)} repos. Generating dashboard...")
    md = generate_markdown(repos)
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(md)
    print("README.md updated successfully.")


if __name__ == "__main__":
    main()
