CREATE SCHEMA IF NOT EXISTS dataset_github_event;

CREATE OR REPLACE VIEW dataset_github_event.v_push_active_repos_24h AS
SELECT
  repo_id,
  repo_name,
  COUNT(*) AS push_event_count,
  COALESCE(SUM(commit_count), 0) AS commit_count,
  COUNT(DISTINCT actor_id) FILTER (WHERE actor_id IS NOT NULL) AS developer_count,
  MAX(created_at) AS latest_push_at
FROM dataset_github_event.github_push_event_detail
WHERE created_at >= now() - INTERVAL '24 hours'
GROUP BY repo_id, repo_name
ORDER BY commit_count DESC, push_event_count DESC, latest_push_at DESC
LIMIT 100;

CREATE OR REPLACE VIEW dataset_github_event.v_starred_repos_detail_24h AS
SELECT
  repo_id,
  repo_name,
  COUNT(*) AS star_count,
  COUNT(DISTINCT actor_id) FILTER (WHERE actor_id IS NOT NULL) AS starring_developer_count,
  MAX(created_at) AS latest_star_at
FROM dataset_github_event.github_watch_event_detail
WHERE created_at >= now() - INTERVAL '24 hours'
  AND action = 'started'
GROUP BY repo_id, repo_name
ORDER BY star_count DESC, latest_star_at DESC
LIMIT 100;

CREATE OR REPLACE VIEW dataset_github_event.v_forked_repos_24h AS
SELECT
  repo_id,
  repo_name,
  COUNT(*) AS fork_count,
  COUNT(DISTINCT actor_id) FILTER (WHERE actor_id IS NOT NULL) AS forking_developer_count,
  MAX(created_at) AS latest_fork_at
FROM dataset_github_event.github_fork_event_detail
WHERE created_at >= now() - INTERVAL '24 hours'
GROUP BY repo_id, repo_name
ORDER BY fork_count DESC, latest_fork_at DESC
LIMIT 100;

CREATE OR REPLACE VIEW dataset_github_event.v_issue_active_repos_24h AS
SELECT
  repo_id,
  repo_name,
  COUNT(*) AS issue_event_count,
  COUNT(*) FILTER (WHERE action = 'opened') AS opened_count,
  COUNT(*) FILTER (WHERE action = 'closed') AS closed_count,
  COUNT(DISTINCT actor_id) FILTER (WHERE actor_id IS NOT NULL) AS developer_count,
  MAX(created_at) AS latest_issue_event_at
FROM dataset_github_event.github_issues_event_detail
WHERE created_at >= now() - INTERVAL '24 hours'
GROUP BY repo_id, repo_name
ORDER BY issue_event_count DESC, opened_count DESC, latest_issue_event_at DESC
LIMIT 100;

CREATE OR REPLACE VIEW dataset_github_event.v_pull_request_active_repos_24h AS
SELECT
  repo_id,
  repo_name,
  COUNT(*) AS pull_request_event_count,
  COUNT(*) FILTER (WHERE action = 'opened') AS opened_count,
  COUNT(*) FILTER (WHERE action = 'closed') AS closed_count,
  COUNT(*) FILTER (WHERE merged IS TRUE) AS merged_count,
  COUNT(DISTINCT actor_id) FILTER (WHERE actor_id IS NOT NULL) AS developer_count,
  MAX(created_at) AS latest_pull_request_event_at
FROM dataset_github_event.github_pull_request_event_detail
WHERE created_at >= now() - INTERVAL '24 hours'
GROUP BY repo_id, repo_name
ORDER BY pull_request_event_count DESC, opened_count DESC, latest_pull_request_event_at DESC
LIMIT 100;

CREATE OR REPLACE VIEW dataset_github_event.v_event_detail_parse_coverage AS
SELECT
  raw.type,
  COUNT(*) AS raw_event_count,
  COUNT(push.event_id) AS push_detail_count,
  COUNT(watch.event_id) AS watch_detail_count,
  COUNT(fork.event_id) AS fork_detail_count,
  COUNT(issues.event_id) AS issues_detail_count,
  COUNT(pr.event_id) AS pull_request_detail_count
FROM dataset_github_event.github_event_raw raw
LEFT JOIN dataset_github_event.github_push_event_detail push
  ON raw.id = push.event_id
LEFT JOIN dataset_github_event.github_watch_event_detail watch
  ON raw.id = watch.event_id
LEFT JOIN dataset_github_event.github_fork_event_detail fork
  ON raw.id = fork.event_id
LEFT JOIN dataset_github_event.github_issues_event_detail issues
  ON raw.id = issues.event_id
LEFT JOIN dataset_github_event.github_pull_request_event_detail pr
  ON raw.id = pr.event_id
WHERE raw.type IN ('PushEvent', 'WatchEvent', 'ForkEvent', 'IssuesEvent', 'PullRequestEvent')
GROUP BY raw.type
ORDER BY raw_event_count DESC;
