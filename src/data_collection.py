import asyncpg
from asyncio import create_task, gather
from typing import Literal
from httpx import AsyncClient
import math
from datetime import datetime

import log

LOG = log.get_logger(__name__)

headers = {"Authorization": "Bearer <token>"}
aclient = AsyncClient(headers=headers)

STORAGE = []

async def get_data(client, url, keyword):
    async def _fetch_repo_data(client, url):
        resp = await client.get(url)
        data = resp.json()
        repo_keys = ["id", "name", "created_at", "language"]
        repositories = []
        items = data["items"]
        repositories = [{key: i[key] for key in repo_keys} for i in items]
        return repositories

    resp = await client.get(url)
    data = resp.json()
    total_count = data.get("total_count")
    pages_num = math.ceil(total_count/100)
    tasks = []

    for page_num in range(1, pages_num + 1):
        repo_url = f"https://api.github.com/search/repositories?q={keyword}+in:file+created:2023-03-22&page={page_num}&per_page=100&sort=stars&order=desc"
        tasks.append(create_task(_fetch_repo_data(aclient, repo_url)))

    finished = await gather(*tasks)

    LOG.info(f"TOTAL: {data.get('total_count')}")

    return sum(finished, [])


async def populate_repositories_table(keyword: str):
    url = f"https://api.github.com/search/repositories?q={keyword}+in:file+created:2023-03-22&per_page=100&sort=stars&order=desc"
    result = await get_data(aclient, url, keyword)
    LOG.info(f"TOTAL RESULT: {len(result)}")
    _ = [x.update({"created_at": datetime.strptime(x["created_at"], "%Y-%m-%dT%H:%M:%SZ"), "keyword": keyword}) for x in result]
    prepared_rows = [tuple(data.values()) for data in result]
    LOG.info(f"TOTAL PREPARED: {len(prepared_rows)}")
    conn = await asyncpg.connect("postgres://docker:docker@postgres:5432/docker")
    statement = f"""
        INSERT INTO repositories (repo_id, repo_name, created_at, lang, keyword) VALUES ($1, $2, $3, $4, $5)
    """
    await conn.executemany(statement, prepared_rows)
    await conn.close()


    for row in prepared_rows:
        print(f"PREPARED REPO data: {row}")


async def get_commits_data(client, url, keyword):
    def _parse_commits(items):
        commit_data = []
        for i in items:
            commit_data.append({"commit_date": i["commit"]["committer"]["date"], "repo_id": i["repository"]["id"], "repo_name": i["repository"]["name"]})
        return commit_data

    async def _fetch_commits_data(client, url):
        resp = await client.get(url)
        data = resp.json()
        items = data["items"]
        commits = _parse_commits(items)
        return commits

    resp = await client.get(url)
    data = resp.json()
    total_count = data.get("total_count")
    pages_num = math.ceil(total_count/100)
    tasks = []

    for page_num in range(1, pages_num + 1):
        commit_url = f"https://api.github.com/search/commits?q={keyword}+committer-date:2023-01-15T00:00:00..2023-01-15T12:00:00&page={page_num}&per_page=100&sort=stars&order=desc"
        tasks.append(create_task(_fetch_commits_data(aclient, commit_url)))

    finished = await gather(*tasks)

    LOG.info(f"TOTAL COMMITS: {data.get('total_count')}")
    return sum(finished, [])



async def populate_commits_table(keyword: str):
    url = f"https://api.github.com/search/commits?q={keyword}+committer-date:2023-01-15T00:00:00..2023-01-15T12:00:00"
    result = await get_commits_data(aclient, url, keyword)

    _ = [x.update({"commit_date": datetime.strptime(x["commit_date"], "%Y-%m-%dT%H:%M:%S.%f%z"), "keyword": keyword}) for x in result]
    prepared_rows = [tuple(data.values()) for data in result]
    LOG.info(f"TOTAL PREPARED COMMITS: {len(prepared_rows)}")
    conn = await asyncpg.connect("postgres://docker:docker@postgres:5432/docker")
    statement = f"""
        INSERT INTO commits (commit_date, repo_id, repo_name, keyword) VALUES ($1, $2, $3, $4)
    """
    await conn.executemany(statement, prepared_rows)
    await conn.close()

    for row in prepared_rows:
        print(f"PREPARED COMMIT data: {row}")


def compose_url(keyword: str, date_range: str, q_params: str, source: Literal["repositories", "commits"]):
    return "https://api.github.com/search/{source}?q={keyword}+{date_range}&{q_params}"
