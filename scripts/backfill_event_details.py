#!/usr/bin/env python3
"""Backfill selected GitHub event detail tables from github_event_raw."""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime
from typing import Any, Iterable

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb


DEFAULT_DATABASE_URL = "postgresql://github:github@localhost:5432/github_dw_analysis"
SUPPORTED_TYPES = (
    "PushEvent",
    "WatchEvent",
    "ForkEvent",
    "IssuesEvent",
    "PullRequestEvent",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Backfill GitHub event detail tables.")
    parser.add_argument(
        "--database-url",
        default=os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL),
        help="PostgreSQL connection URL. Defaults to DATABASE_URL or local docker compose settings.",
    )
    parser.add_argument(
        "--event-type",
        action="append",
        choices=SUPPORTED_TYPES,
        help="Limit backfill to one or more event types.",
    )
    parser.add_argument("--batch-size", type=int, default=5000)
    parser.add_argument("--limit", type=int, help="Maximum raw events to scan.")
    return parser.parse_args()


def parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def as_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def actor(raw: dict[str, Any]) -> dict[str, Any]:
    value = raw.get("actor")
    return value if isinstance(value, dict) else {}


def repo(raw: dict[str, Any]) -> dict[str, Any]:
    value = raw.get("repo")
    return value if isinstance(value, dict) else {}


def payload(raw: dict[str, Any]) -> dict[str, Any]:
    value = raw.get("payload")
    return value if isinstance(value, dict) else {}


def common(raw: dict[str, Any]) -> tuple[Any, ...]:
    raw_actor = actor(raw)
    raw_repo = repo(raw)
    return (
        as_int(raw.get("id")),
        as_int(raw_repo.get("id")),
        raw_repo.get("name"),
        as_int(raw_actor.get("id")),
        raw_actor.get("login"),
        parse_timestamp(raw.get("created_at")),
    )


def commit_shas(raw_payload: dict[str, Any]) -> list[str]:
    commits = raw_payload.get("commits")
    if not isinstance(commits, list):
        return []
    shas: list[str] = []
    for commit in commits:
        if isinstance(commit, dict) and commit.get("sha"):
            shas.append(str(commit["sha"]))
    return shas


def parse_push(raw: dict[str, Any]) -> tuple[Any, ...]:
    raw_payload = payload(raw)
    shas = commit_shas(raw_payload)
    return common(raw) + (
        as_int(raw_payload.get("push_id")),
        raw_payload.get("ref"),
        raw_payload.get("head"),
        raw_payload.get("before"),
        len(shas),
        as_int(raw_payload.get("distinct_size")),
        shas,
    )


def parse_watch(raw: dict[str, Any]) -> tuple[Any, ...]:
    return common(raw) + (payload(raw).get("action"),)


def parse_fork(raw: dict[str, Any]) -> tuple[Any, ...]:
    forkee = payload(raw).get("forkee")
    if not isinstance(forkee, dict):
        forkee = {}
    owner = forkee.get("owner")
    if not isinstance(owner, dict):
        owner = {}
    return common(raw) + (
        as_int(forkee.get("id")),
        forkee.get("full_name"),
        owner.get("login"),
        forkee.get("html_url"),
    )


def parse_issues(raw: dict[str, Any]) -> tuple[Any, ...]:
    raw_payload = payload(raw)
    issue = raw_payload.get("issue")
    if not isinstance(issue, dict):
        issue = {}
    user = issue.get("user")
    if not isinstance(user, dict):
        user = {}
    return common(raw) + (
        raw_payload.get("action"),
        as_int(issue.get("id")),
        as_int(issue.get("number")),
        issue.get("title"),
        issue.get("state"),
        user.get("login"),
        as_int(issue.get("comments")),
        Jsonb(issue.get("labels") or []),
    )


def parse_pull_request(raw: dict[str, Any]) -> tuple[Any, ...]:
    raw_payload = payload(raw)
    pr = raw_payload.get("pull_request")
    if not isinstance(pr, dict):
        pr = {}
    user = pr.get("user")
    if not isinstance(user, dict):
        user = {}
    requested_reviewers = pr.get("requested_reviewers")
    if not isinstance(requested_reviewers, list):
        requested_reviewers = []
    return common(raw) + (
        raw_payload.get("action"),
        as_int(pr.get("id")),
        as_int(pr.get("number")),
        pr.get("title"),
        pr.get("state"),
        user.get("login"),
        pr.get("merged"),
        parse_timestamp(pr.get("merged_at")),
        as_int(pr.get("additions")),
        as_int(pr.get("deletions")),
        as_int(pr.get("changed_files")),
        as_int(pr.get("commits")),
        as_int(pr.get("review_comments")),
        len(requested_reviewers),
    )


INSERT_SQL = {
    "PushEvent": """
        INSERT INTO dataset_github_event.github_push_event_detail (
          event_id, repo_id, repo_name, actor_id, actor_login, created_at,
          push_id, ref, head, before, commit_count, distinct_commit_count, commit_shas
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (event_id) DO UPDATE SET
          repo_id = EXCLUDED.repo_id,
          repo_name = EXCLUDED.repo_name,
          actor_id = EXCLUDED.actor_id,
          actor_login = EXCLUDED.actor_login,
          created_at = EXCLUDED.created_at,
          push_id = EXCLUDED.push_id,
          ref = EXCLUDED.ref,
          head = EXCLUDED.head,
          before = EXCLUDED.before,
          commit_count = EXCLUDED.commit_count,
          distinct_commit_count = EXCLUDED.distinct_commit_count,
          commit_shas = EXCLUDED.commit_shas,
          parsed_at = now()
    """,
    "WatchEvent": """
        INSERT INTO dataset_github_event.github_watch_event_detail (
          event_id, repo_id, repo_name, actor_id, actor_login, created_at, action
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (event_id) DO UPDATE SET
          repo_id = EXCLUDED.repo_id,
          repo_name = EXCLUDED.repo_name,
          actor_id = EXCLUDED.actor_id,
          actor_login = EXCLUDED.actor_login,
          created_at = EXCLUDED.created_at,
          action = EXCLUDED.action,
          parsed_at = now()
    """,
    "ForkEvent": """
        INSERT INTO dataset_github_event.github_fork_event_detail (
          event_id, repo_id, repo_name, actor_id, actor_login, created_at,
          forkee_id, forkee_full_name, forkee_owner_login, forkee_html_url
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (event_id) DO UPDATE SET
          repo_id = EXCLUDED.repo_id,
          repo_name = EXCLUDED.repo_name,
          actor_id = EXCLUDED.actor_id,
          actor_login = EXCLUDED.actor_login,
          created_at = EXCLUDED.created_at,
          forkee_id = EXCLUDED.forkee_id,
          forkee_full_name = EXCLUDED.forkee_full_name,
          forkee_owner_login = EXCLUDED.forkee_owner_login,
          forkee_html_url = EXCLUDED.forkee_html_url,
          parsed_at = now()
    """,
    "IssuesEvent": """
        INSERT INTO dataset_github_event.github_issues_event_detail (
          event_id, repo_id, repo_name, actor_id, actor_login, created_at,
          action, issue_id, issue_number, issue_title, issue_state,
          issue_author_login, comments_count, labels
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (event_id) DO UPDATE SET
          repo_id = EXCLUDED.repo_id,
          repo_name = EXCLUDED.repo_name,
          actor_id = EXCLUDED.actor_id,
          actor_login = EXCLUDED.actor_login,
          created_at = EXCLUDED.created_at,
          action = EXCLUDED.action,
          issue_id = EXCLUDED.issue_id,
          issue_number = EXCLUDED.issue_number,
          issue_title = EXCLUDED.issue_title,
          issue_state = EXCLUDED.issue_state,
          issue_author_login = EXCLUDED.issue_author_login,
          comments_count = EXCLUDED.comments_count,
          labels = EXCLUDED.labels,
          parsed_at = now()
    """,
    "PullRequestEvent": """
        INSERT INTO dataset_github_event.github_pull_request_event_detail (
          event_id, repo_id, repo_name, actor_id, actor_login, created_at,
          action, pull_request_id, pull_request_number, pull_request_title,
          pull_request_state, pull_request_author_login, merged, merged_at,
          additions, deletions, changed_files, commits_count,
          review_comments_count, requested_reviewers_count
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (event_id) DO UPDATE SET
          repo_id = EXCLUDED.repo_id,
          repo_name = EXCLUDED.repo_name,
          actor_id = EXCLUDED.actor_id,
          actor_login = EXCLUDED.actor_login,
          created_at = EXCLUDED.created_at,
          action = EXCLUDED.action,
          pull_request_id = EXCLUDED.pull_request_id,
          pull_request_number = EXCLUDED.pull_request_number,
          pull_request_title = EXCLUDED.pull_request_title,
          pull_request_state = EXCLUDED.pull_request_state,
          pull_request_author_login = EXCLUDED.pull_request_author_login,
          merged = EXCLUDED.merged,
          merged_at = EXCLUDED.merged_at,
          additions = EXCLUDED.additions,
          deletions = EXCLUDED.deletions,
          changed_files = EXCLUDED.changed_files,
          commits_count = EXCLUDED.commits_count,
          review_comments_count = EXCLUDED.review_comments_count,
          requested_reviewers_count = EXCLUDED.requested_reviewers_count,
          parsed_at = now()
    """,
}

PARSERS = {
    "PushEvent": parse_push,
    "WatchEvent": parse_watch,
    "ForkEvent": parse_fork,
    "IssuesEvent": parse_issues,
    "PullRequestEvent": parse_pull_request,
}


def selected_types(args: argparse.Namespace) -> tuple[str, ...]:
    if not args.event_type:
        return SUPPORTED_TYPES
    return tuple(dict.fromkeys(args.event_type))


def raw_rows(conn: psycopg.Connection[Any], types: tuple[str, ...], limit: int | None) -> Iterable[dict[str, Any]]:
    query = """
        SELECT id, type, raw_event
        FROM dataset_github_event.github_event_raw
        WHERE type = ANY(%s)
        ORDER BY created_at, id
    """
    params: list[Any] = [list(types)]
    if limit is not None:
        query += " LIMIT %s"
        params.append(limit)
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(query, params)
        yield from cur


def flush_batch(conn: psycopg.Connection[Any], event_type: str, batch: list[tuple[Any, ...]]) -> int:
    if not batch:
        return 0
    with conn.cursor() as cur:
        cur.executemany(INSERT_SQL[event_type], batch)
    conn.commit()
    return len(batch)


def backfill(conn: psycopg.Connection[Any], types: tuple[str, ...], batch_size: int, limit: int | None) -> dict[str, int]:
    batches: dict[str, list[tuple[Any, ...]]] = {event_type: [] for event_type in types}
    counts: dict[str, int] = {event_type: 0 for event_type in types}

    for row in raw_rows(conn, types, limit):
        event_type = row["type"]
        raw = row["raw_event"]
        parsed = PARSERS[event_type](raw)
        batches[event_type].append(parsed)
        if len(batches[event_type]) >= batch_size:
            counts[event_type] += flush_batch(conn, event_type, batches[event_type])
            batches[event_type].clear()

    for event_type, batch in batches.items():
        counts[event_type] += flush_batch(conn, event_type, batch)

    return counts


def main() -> int:
    args = parse_args()
    if args.batch_size < 1:
        raise SystemExit("--batch-size must be greater than 0")

    types = selected_types(args)
    with psycopg.connect(args.database_url) as conn:
        counts = backfill(conn, types, args.batch_size, args.limit)

    for event_type in types:
        print(f"{event_type}: upserted={counts[event_type]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
