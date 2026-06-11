CREATE SCHEMA IF NOT EXISTS dataset_github_event;

CREATE TABLE IF NOT EXISTS dataset_github_event.github_push_event_detail (
  event_id bigint PRIMARY KEY REFERENCES dataset_github_event.github_event (id),
  repo_id bigint,
  repo_name text,
  actor_id bigint,
  actor_login text,
  created_at timestamp with time zone NOT NULL,
  push_id bigint,
  ref text,
  head text,
  before text,
  commit_count integer NOT NULL DEFAULT 0,
  distinct_commit_count integer,
  commit_shas text[],
  parsed_at timestamp with time zone NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS dataset_github_event.github_watch_event_detail (
  event_id bigint PRIMARY KEY REFERENCES dataset_github_event.github_event (id),
  repo_id bigint,
  repo_name text,
  actor_id bigint,
  actor_login text,
  created_at timestamp with time zone NOT NULL,
  action text,
  parsed_at timestamp with time zone NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS dataset_github_event.github_fork_event_detail (
  event_id bigint PRIMARY KEY REFERENCES dataset_github_event.github_event (id),
  repo_id bigint,
  repo_name text,
  actor_id bigint,
  actor_login text,
  created_at timestamp with time zone NOT NULL,
  forkee_id bigint,
  forkee_full_name text,
  forkee_owner_login text,
  forkee_html_url text,
  parsed_at timestamp with time zone NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS dataset_github_event.github_issues_event_detail (
  event_id bigint PRIMARY KEY REFERENCES dataset_github_event.github_event (id),
  repo_id bigint,
  repo_name text,
  actor_id bigint,
  actor_login text,
  created_at timestamp with time zone NOT NULL,
  action text,
  issue_id bigint,
  issue_number integer,
  issue_title text,
  issue_state text,
  issue_author_login text,
  comments_count integer,
  labels jsonb,
  parsed_at timestamp with time zone NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS dataset_github_event.github_pull_request_event_detail (
  event_id bigint PRIMARY KEY REFERENCES dataset_github_event.github_event (id),
  repo_id bigint,
  repo_name text,
  actor_id bigint,
  actor_login text,
  created_at timestamp with time zone NOT NULL,
  action text,
  pull_request_id bigint,
  pull_request_number integer,
  pull_request_title text,
  pull_request_state text,
  pull_request_author_login text,
  merged boolean,
  merged_at timestamp with time zone,
  additions integer,
  deletions integer,
  changed_files integer,
  commits_count integer,
  review_comments_count integer,
  requested_reviewers_count integer,
  parsed_at timestamp with time zone NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_push_event_detail_repo_created_at
ON dataset_github_event.github_push_event_detail (repo_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_push_event_detail_actor_created_at
ON dataset_github_event.github_push_event_detail (actor_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_watch_event_detail_repo_created_at
ON dataset_github_event.github_watch_event_detail (repo_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_fork_event_detail_repo_created_at
ON dataset_github_event.github_fork_event_detail (repo_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_issues_event_detail_repo_created_at
ON dataset_github_event.github_issues_event_detail (repo_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_issues_event_detail_action_created_at
ON dataset_github_event.github_issues_event_detail (action, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_pull_request_event_detail_repo_created_at
ON dataset_github_event.github_pull_request_event_detail (repo_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_pull_request_event_detail_action_created_at
ON dataset_github_event.github_pull_request_event_detail (action, created_at DESC);
