CREATE SCHEMA IF NOT EXISTS dataset_github_event;

CREATE TABLE IF NOT EXISTS dataset_github_event.github_event (
  id bigint PRIMARY KEY,
  actor_id bigint,
  actor_login text,
  repo_id bigint,
  repo_name text,
  org_id bigint,
  org_login text,
  type text,
  created_at timestamp with time zone NOT NULL,
  action text,
  commit_id text,
  member_id bigint,
  language text
);

CREATE TABLE IF NOT EXISTS dataset_github_event.github_archive_ingest_log (
  archive_hour timestamp with time zone PRIMARY KEY,
  archive_url text NOT NULL,
  status text NOT NULL,
  event_count integer NOT NULL DEFAULT 0,
  inserted_count integer NOT NULL DEFAULT 0,
  error_message text,
  started_at timestamp with time zone NOT NULL DEFAULT now(),
  finished_at timestamp with time zone
);

CREATE INDEX IF NOT EXISTS idx_github_event_created_at
ON dataset_github_event.github_event (created_at DESC);

CREATE INDEX IF NOT EXISTS idx_github_event_type_created_at
ON dataset_github_event.github_event (type, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_github_event_repo_created_at
ON dataset_github_event.github_event (repo_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_github_event_actor_created_at
ON dataset_github_event.github_event (actor_id, created_at DESC);
