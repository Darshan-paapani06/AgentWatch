#!/usr/bin/env python3
"""AgentWatch Railway deployment script.
Uses Railway GraphQL API to verify credentials, create a project, and expose deployment IDs.
Run: python scripts/railway_deploy.py <RAILWAY_TOKEN>
"""

from __future__ import annotations
import argparse
import json
import textwrap
from pathlib import Path

import httpx

API = "https://backboard.railway.app/graphql/v2"
PROJECT_NAME = "agentwatch"
OUTPUT_FILE = Path("railway_ids.json")


def gql(token: str, query: str, variables: dict | None = None) -> dict:
    response = httpx.post(
        API,
        json={"query": query, "variables": variables or {}},
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    if "errors" in payload:
        raise RuntimeError(f"GraphQL error: {payload['errors']}")
    return payload["data"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Deploy AgentWatch to Railway.")
    parser.add_argument("token", help="Railway API token")
    return parser.parse_args()


def get_current_user(token: str) -> dict:
    data = gql(token, "{ me { name email } }")
    return data["me"]


def get_existing_projects(token: str) -> dict[str, str]:
    data = gql(token, "{ me { projects { edges { node { id name } } } } }")
    return {node["name"]: node["id"] for node in (edge["node"] for edge in data["me"]["projects"]["edges"])}


def create_project(token: str, name: str) -> str:
    query = textwrap.dedent(
        """
        mutation($name: String!) {
          projectCreate(input: { name: $name, isPublic: false }) {
            id
          }
        }
        """
    )
    data = gql(token, query, {"name": name})
    return data["projectCreate"]["id"]


def get_environment_id(token: str, project_id: str) -> str:
    query = textwrap.dedent(
        """
        query($id: String!) {
          project(id: $id) {
            environments {
              edges { node { id name } }
            }
          }
        }
        """
    )
    data = gql(token, query, {"id": project_id})
    return data["project"]["environments"]["edges"][0]["node"]["id"]


def get_services(token: str, project_id: str) -> dict[str, str]:
    query = textwrap.dedent(
        """
        query($id: String!) {
          project(id: $id) {
            services {
              edges { node { id name } }
            }
          }
        }
        """
    )
    data = gql(token, query, {"id": project_id})
    return {node["name"]: node["id"] for node in (edge["node"] for edge in data["project"]["services"]["edges"])}


def save_ids(project_id: str, env_id: str, services: dict[str, str]) -> None:
    OUTPUT_FILE.write_text(
        json.dumps({"project_id": project_id, "env_id": env_id, "services": services}, indent=2)
    )


def main() -> None:
    args = parse_args()
    token = args.token

    user = get_current_user(token)
    print(f"Logged in as: {user['name']} ({user['email']})")

    existing_projects = get_existing_projects(token)
    print(f"Existing projects: {list(existing_projects) or ['none']}")

    project_id = existing_projects.get(PROJECT_NAME) or create_project(token, PROJECT_NAME)
    print(f"Using project: {project_id}")

    env_id = get_environment_id(token, project_id)
    print(f"Environment: {env_id}")

    services = get_services(token, project_id)
    print(f"Existing services: {list(services) or ['none']}")

    print("\nAll pre-checks done. Project and environment ready.")
    print(f"Project ID:     {project_id}")
    print(f"Environment ID: {env_id}")
    print("\nNext: use `railway link` + `railway up` to deploy each service.")
    print("Or paste these IDs into the Railway dashboard to finish deployment.")

    save_ids(project_id, env_id, services)
    print(f"\nWrote {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
