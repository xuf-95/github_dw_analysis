#!/usr/bin/env python3
"""Ingest GitHub Archive hourly event files into PostgreSQL."""

from __future__ import annotations

import argparse
import gzip
import json
import os
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable

import psycopg
from psycopg.types.json import Jsonb


BATCH_SIZE = 1000
ARCHIVE_BASE_URL = "https://data.gharchive.org"
DEFAULT_DATABASE_URL = "postgresql://github:github@localhost:5432/github_dw_analysis"


@dataclass(frozen=True)
class ParsedEvent:
    id: int
    actor_id: int | None
    actor_login: str | None
    repo_id: int | None
    repo_name: str | None
    org_id: int | None
    org_login: str | None
    type: str | None
    created_at: datetime
    action: str | None
    commit_id: str | None
    member_id: int | None
    language: str | None


@dataclass(frozen=True)
class IngestEvent:
    parsed: ParsedEvent
    raw_event: dict[str, Any]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest GitHub Archive events.")
    parser.add_argument(
        "--hour",
        action="append",
        help="Archive hour in UTC, formatted as YYYY-MM-DD-H. Can be passed multiple times.",
    )
    parser.add_argument(
        "--last-hours",
        type=int,
        help="Ingest the latest completed N archive hours in UTC.",
    )
    parser.add_argument(
        "--start-hour",
        help="Start archive hour in UTC, formatted as YYYY-MM-DD-H. Used with --end-hour.",
    )
    parser.add_argument(
        "--end-hour",
        help="End archive hour in UTC, formatted as YYYY-MM-DD-H. Inclusive.",
    )
    parser.add_argument(
        "--retry-failed",
        action="store_true",
        help="Retry all hours currently marked as failed in the ingest log.",
    )
    parser.add_argument(
        "--database-url",
        default=os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL),
        help="PostgreSQL connection URL. Defaults to DATABASE_URL or local docker compose settings.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-ingest hours even when the ingest log already marks them as success.",
    )
    return parser.parse_args()


def completed_utc_hour(now: datetime | None = None) -> datetime:
    current = now or datetime.now(timezone.utc)
    return current.replace(minute=0, second=0, microsecond=0) - timedelta(hours=1)


def parse_archive_hour(value: str) -> datetime:
    try:
        parsed = datetime.strptime(value, "%Y-%m-%d-%H")
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"Invalid hour '{value}', expected YYYY-MM-DD-H"
        ) from exc
    return parsed.replace(tzinfo=timezone.utc)


def hour_range(start: datetime, end: datetime) -> Iterable[datetime]:
    current = start
    while current <= end:
        yield current
        current += timedelta(hours=1)


def failed_hours(conn: psycopg.Connection[Any]) -> list[datetime]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT archive_hour
            FROM dataset_github_event.github_archive_ingest_log
            WHERE status = 'failed'
            ORDER BY archive_hour
            """
        )
        return [row[0] for row in cur.fetchall()]


def resolve_hours(args: argparse.Namespace, conn: psycopg.Connection[Any]) -> list[datetime]:
    hours: set[datetime] = set()

    if args.hour:
        hours.update(parse_archive_hour(value) for value in args.hour)

    if args.start_hour or args.end_hour:
        if not args.start_hour or not args.end_hour:
            raise SystemExit("--start-hour and --end-hour must be used together")
        start = parse_archive_hour(args.start_hour)
        end = parse_archive_hour(args.end_hour)
        if start > end:
            raise SystemExit("--start-hour must be earlier than or equal to --end-hour")
        hours.update(hour_range(start, end))

    if args.last_hours:
        if args.last_hours < 1:
            raise SystemExit("--last-hours must be greater than 0")
        latest = completed_utc_hour()
        hours.update(latest - timedelta(hours=offset) for offset in range(args.last_hours))

    if args.retry_failed:
        hours.update(failed_hours(conn))

    if not hours:
        hours.add(completed_utc_hour())

    return sorted(hours)


def archive_url(hour: datetime) -> str:
    return f"{ARCHIVE_BASE_URL}/{hour.year}-{hour.month:02d}-{hour.day:02d}-{hour.hour}.json.gz"


def read_archive_lines(url: str) -> Iterable[bytes]:
    request = urllib.request.Request(url, headers={"User-Agent": "github_dw_analysis/0.1"})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            with gzip.GzipFile(fileobj=response) as archive:
                yield from archive
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"HTTP {exc.code} while downloading {url}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Could not download {url}: {exc.reason}") from exc


def parse_created_at(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def remove_nul_chars(value: Any) -> Any:
    if isinstance(value, str):
        return value.replace("\x00", "")
    if isinstance(value, list):
        return [remove_nul_chars(item) for item in value]
    if isinstance(value, dict):
        return {key: remove_nul_chars(item) for key, item in value.items()}
    return value


def first_commit_id(payload: dict[str, Any]) -> str | None:
    commits = payload.get("commits")
    if not isinstance(commits, list) or not commits:
        return None
    first_commit = commits[0]
    if not isinstance(first_commit, dict):
        return None
    commit_id = first_commit.get("sha")
    return str(commit_id) if commit_id else None


def parse_event(raw_event: dict[str, Any]) -> ParsedEvent:
    actor = raw_event.get("actor") or {}
    repo = raw_event.get("repo") or {}
    org = raw_event.get("org") or {}
    payload = raw_event.get("payload") or {}
    member = payload.get("member") or {}
    repository = payload.get("repository") or {}

    return ParsedEvent(
        id=int(raw_event["id"]),
        actor_id=actor.get("id"),
        actor_login=actor.get("login"),
        repo_id=repo.get("id"),
        repo_name=repo.get("name"),
        org_id=org.get("id"),
        org_login=org.get("login"),
        type=raw_event.get("type"),
        created_at=parse_created_at(raw_event["created_at"]),
        action=payload.get("action"),
        commit_id=first_commit_id(payload),
        member_id=member.get("id"),
        language=repository.get("language"),
    )


def event_row(event: ParsedEvent) -> tuple[Any, ...]:
    return (
        event.id,
        event.actor_id,
        event.actor_login,
        event.repo_id,
        event.repo_name,
        event.org_id,
        event.org_login,
        event.type,
        event.created_at,
        event.action,
        event.commit_id,
        event.member_id,
        event.language,
    )


def raw_event_row(event: IngestEvent, hour: datetime) -> tuple[Any, ...]:
    return (
        event.parsed.id,
        hour,
        event.parsed.type,
        event.parsed.created_at,
        Jsonb(event.raw_event),
    )


def already_ingested(conn: psycopg.Connection[Any], hour: datetime) -> bool:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT status
            FROM dataset_github_event.github_archive_ingest_log
            WHERE archive_hour = %s
            """,
            (hour,),
        )
        row = cur.fetchone()
    return bool(row and row[0] == "success")


def mark_started(conn: psycopg.Connection[Any], hour: datetime, url: str) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO dataset_github_event.github_archive_ingest_log (
              archive_hour, archive_url, status, event_count, inserted_count,
              raw_inserted_count, error_message, started_at, finished_at
            )
            VALUES (%s, %s, 'running', 0, 0, 0, NULL, now(), NULL)
            ON CONFLICT (archive_hour) DO UPDATE SET
              archive_url = EXCLUDED.archive_url,
              status = 'running',
              event_count = 0,
              inserted_count = 0,
              raw_inserted_count = 0,
              error_message = NULL,
              started_at = now(),
              finished_at = NULL
            """,
            (hour, url),
        )
    conn.commit()


def mark_finished(
    conn: psycopg.Connection[Any],
    hour: datetime,
    status: str,
    event_count: int,
    inserted_count: int,
    raw_inserted_count: int,
    error_message: str | None = None,
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE dataset_github_event.github_archive_ingest_log
            SET status = %s,
                event_count = %s,
                inserted_count = %s,
                raw_inserted_count = %s,
                error_message = %s,
                finished_at = now()
            WHERE archive_hour = %s
            """,
            (status, event_count, inserted_count, raw_inserted_count, error_message, hour),
        )
    conn.commit()


def insert_event_batch(conn: psycopg.Connection[Any], batch: list[IngestEvent]) -> int:
    if not batch:
        return 0

    with conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO dataset_github_event.github_event (
              id, actor_id, actor_login, repo_id, repo_name, org_id, org_login,
              type, created_at, action, commit_id, member_id, language
            )
            VALUES (
              %s, %s, %s, %s, %s, %s, %s,
              %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (id) DO NOTHING
            """,
            [event_row(event.parsed) for event in batch],
        )
        inserted = cur.rowcount if cur.rowcount >= 0 else 0
    conn.commit()
    return inserted


def insert_raw_batch(
    conn: psycopg.Connection[Any],
    batch: list[IngestEvent],
    hour: datetime,
) -> int:
    if not batch:
        return 0

    with conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO dataset_github_event.github_event_raw (
              id, archive_hour, type, created_at, raw_event
            )
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
            """,
            [raw_event_row(event, hour) for event in batch],
        )
        inserted = cur.rowcount if cur.rowcount >= 0 else 0
    conn.commit()
    return inserted


def insert_batch(
    conn: psycopg.Connection[Any],
    batch: list[IngestEvent],
    hour: datetime,
) -> tuple[int, int]:
    raw_inserted = insert_raw_batch(conn, batch, hour)
    fact_inserted = insert_event_batch(conn, batch)
    return fact_inserted, raw_inserted


def ingest_hour(conn: psycopg.Connection[Any], hour: datetime, force: bool) -> None:
    url = archive_url(hour)
    if not force and already_ingested(conn, hour):
        print(f"skip {hour.isoformat()} already ingested")
        return

    print(f"ingest {hour.isoformat()} from {url}")
    mark_started(conn, hour, url)

    event_count = 0
    inserted_count = 0
    raw_inserted_count = 0
    batch: list[IngestEvent] = []

    try:
        for line in read_archive_lines(url):
            if not line.strip():
                continue
            raw_event = remove_nul_chars(json.loads(line))
            batch.append(IngestEvent(parsed=parse_event(raw_event), raw_event=raw_event))
            event_count += 1

            if len(batch) >= BATCH_SIZE:
                fact_inserted, raw_inserted = insert_batch(conn, batch, hour)
                inserted_count += fact_inserted
                raw_inserted_count += raw_inserted
                batch.clear()

        fact_inserted, raw_inserted = insert_batch(conn, batch, hour)
        inserted_count += fact_inserted
        raw_inserted_count += raw_inserted
        mark_finished(conn, hour, "success", event_count, inserted_count, raw_inserted_count)
        print(
            f"done {hour.isoformat()} events={event_count} "
            f"inserted={inserted_count} raw_inserted={raw_inserted_count}"
        )
    except Exception as exc:
        conn.rollback()
        mark_finished(
            conn,
            hour,
            "failed",
            event_count,
            inserted_count,
            raw_inserted_count,
            str(exc),
        )
        raise


def main() -> int:
    args = parse_args()

    with psycopg.connect(args.database_url) as conn:
        hours = resolve_hours(args, conn)
        for hour in hours:
            ingest_hour(conn, hour, args.force)

    return 0


if __name__ == "__main__":
    sys.exit(main())
