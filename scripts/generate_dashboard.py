import requests
import os

ORG = "oe-alliance-plugins"
TOKEN = os.environ.get("ORG_PAT")
HEADERS = {"Authorization": f"token {TOKEN}"}


def get_repos():
    query = """
    query($org: String!, $cursor: String) {
      organization(login: $org) {
        repositories(first: 100, after: $cursor) {
          pageInfo {
            hasNextPage
            endCursor
          }
          nodes {
            name
            url
          }
        }
      }
    }
    """

    repos = []
    cursor = None

    while True:
        r = requests.post(
            "https://api.github.com/graphql",
            headers=HEADERS,
            json={"query": query, "variables": {"org": ORG, "cursor": cursor}},
        )
        r.raise_for_status()
        data = r.json()["data"]["organization"]["repositories"]

        repos.extend(data["nodes"])

        if not data["pageInfo"]["hasNextPage"]:
            break

        cursor = data["pageInfo"]["endCursor"]

    return repos


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


def get_latest_run(repo, workflow_file):
    url = f"https://api.github.com/repos/{ORG}/{repo}/actions/workflows/{workflow_file}/runs?per_page=1"
    r = requests.get(url, headers=HEADERS)

    if r.status_code != 200:
        return "-", "", "-"

    runs = r.json().get("workflow_runs", [])
    if not runs:
        return "-", "", "-"

    run = runs[0]
    status = "✅" if run["conclusion"] == "success" else "❌"

    return status, run["html_url"], run["updated_at"]


def get_last_workflows(repo_name):
    ruff, ruff_url, ruff_time = get_latest_run(repo_name, "ruff.yml")
    lint, lint_url, lint_time = get_latest_run(repo_name, "pylint.yml")

    last_update = max(ruff_time, lint_time)

    return ruff, lint, ruff_url, lint_url, last_update


def generate_markdown(repos):
    repo_data = []

    for repo in repos:
        name = repo["name"]
        repo_url = repo["url"]

        ruff, lint, ruff_url, lint_url, updated = get_last_workflows(name)

        repo_data.append({
            "name": name,
            "url": repo_url,
            "ruff": ruff,
            "lint": lint,
            "ruff_url": ruff_url,
            "lint_url": lint_url,
            "updated": updated
        })

    sorted_repos = sort_repos_by_status(repo_data)

    lines = [
        "# Org Dashboard\n",
        "| Repo | Ruff | Lint | Last Update |",
        "| --- | --- | --- | --- |"
    ]

    for repo in sorted_repos:
        repo_link = f"[{repo['name']}]({repo['url']})"

        ruff_link = repo["ruff"]
        if repo["ruff_url"]:
            ruff_link = f"[{repo['ruff']}]({repo['ruff_url']})"

        lint_link = repo["lint"]
        if repo["lint_url"]:
            lint_link = f"[{repo['lint']}]({repo['lint_url']})"

        lines.append(
            f"| {repo_link} | {ruff_link} | {lint_link} | {repo['updated']} |"
        )

    return "\n".join(lines)


def main():
    print("Fetching repos...")
    repos = get_repos()
    repos = [r for r in repos if r["name"] != ".github"]
    print(f"Found {len(repos)} repos. Generating dashboard...")
    md = generate_markdown(repos)
    with open("profile/README.md", "w", encoding="utf-8") as f:
        f.write(md)
    print("README.md updated successfully.")


if __name__ == "__main__":
    main()
