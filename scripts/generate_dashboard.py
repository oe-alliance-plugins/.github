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


def generate_markdown(repos):
    repo_data = []

    for repo in repos:
        name = repo["name"]
        repo_url = repo["url"]

        repo_data.append({
            "name": name,
            "url": repo_url
        })

    sorted_repos = sorted(repo_data, key=lambda x: x['name'].lower())

    lines = [
        "# Org Dashboard\n",
        "| Repo | Ruff | Lint | Sonar |",
        "| --- | --- | --- | --- |"
    ]

    for repo in sorted_repos:
        repo_link = f"[{repo['name']}]({repo['url']})"

        # Ruff Badge
        ruff_badge = f"[![Ruff Status](https://github.com/{ORG}/{repo['name']}/actions/workflows/ruff.yml/badge.svg)](https://github.com/{ORG}/{repo['name']}/actions/workflows/ruff.yml)"

        # Lint Badge
        lint_badge = f"[![Lint Status](https://github.com/{ORG}/{repo['name']}/actions/workflows/pylint.yml/badge.svg)](https://github.com/{ORG}/{repo['name']}/actions/workflows/pylint.yml)"

        # Sonar Badge (falls vorhanden)
        sonar_project = f"oe-alliance-plugins_{repo['name']}"
        sonar_badge = f"[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project={sonar_project}&metric=alert_status)](https://sonarcloud.io/summary/new_code?id={sonar_project})"

        lines.append(
            f"| {repo_link} | {ruff_badge} | {lint_badge} | {sonar_badge} |"
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
