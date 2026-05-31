CREATE SCHEMA IF NOT EXISTS dataset_github_event;

CREATE OR REPLACE VIEW dataset_github_event.v_ingest_hourly_status AS
SELECT
  archive_hour,
  archive_url,
  status,
  event_count,
  inserted_count,
  raw_inserted_count,
  started_at,
  finished_at,
  finished_at - started_at AS duration,
  error_message
FROM dataset_github_event.github_archive_ingest_log
ORDER BY archive_hour DESC;

CREATE OR REPLACE VIEW dataset_github_event.v_failed_ingest_hours AS
SELECT
  archive_hour,
  archive_url,
  event_count,
  inserted_count,
  raw_inserted_count,
  error_message,
  started_at,
  finished_at
FROM dataset_github_event.github_archive_ingest_log
WHERE status = 'failed'
ORDER BY archive_hour DESC;

CREATE OR REPLACE VIEW dataset_github_event.v_event_hourly_quality AS
SELECT
  date_trunc('hour', created_at) AS event_hour,
  COUNT(*) AS event_count,
  COUNT(DISTINCT id) AS distinct_event_count,
  COUNT(DISTINCT actor_id) FILTER (WHERE actor_id IS NOT NULL) AS developer_count,
  COUNT(DISTINCT repo_id) FILTER (WHERE repo_id IS NOT NULL) AS repo_count,
  COUNT(*) FILTER (WHERE actor_id IS NULL) AS missing_actor_id_count,
  COUNT(*) FILTER (WHERE repo_id IS NULL) AS missing_repo_id_count,
  COUNT(*) FILTER (WHERE type IS NULL) AS missing_type_count
FROM dataset_github_event.github_event
GROUP BY date_trunc('hour', created_at)
ORDER BY event_hour DESC;

CREATE OR REPLACE VIEW dataset_github_event.v_event_field_null_rate AS
SELECT *
FROM (
  SELECT 'actor_id' AS field_name, COUNT(*) FILTER (WHERE actor_id IS NULL) AS null_count, COUNT(*) AS total_count FROM dataset_github_event.github_event
  UNION ALL
  SELECT 'actor_login', COUNT(*) FILTER (WHERE actor_login IS NULL), COUNT(*) FROM dataset_github_event.github_event
  UNION ALL
  SELECT 'repo_id', COUNT(*) FILTER (WHERE repo_id IS NULL), COUNT(*) FROM dataset_github_event.github_event
  UNION ALL
  SELECT 'repo_name', COUNT(*) FILTER (WHERE repo_name IS NULL), COUNT(*) FROM dataset_github_event.github_event
  UNION ALL
  SELECT 'org_id', COUNT(*) FILTER (WHERE org_id IS NULL), COUNT(*) FROM dataset_github_event.github_event
  UNION ALL
  SELECT 'org_login', COUNT(*) FILTER (WHERE org_login IS NULL), COUNT(*) FROM dataset_github_event.github_event
  UNION ALL
  SELECT 'action', COUNT(*) FILTER (WHERE action IS NULL), COUNT(*) FROM dataset_github_event.github_event
  UNION ALL
  SELECT 'commit_id', COUNT(*) FILTER (WHERE commit_id IS NULL), COUNT(*) FROM dataset_github_event.github_event
  UNION ALL
  SELECT 'member_id', COUNT(*) FILTER (WHERE member_id IS NULL), COUNT(*) FROM dataset_github_event.github_event
  UNION ALL
  SELECT 'language', COUNT(*) FILTER (WHERE language IS NULL), COUNT(*) FROM dataset_github_event.github_event
) fields
CROSS JOIN LATERAL (
  SELECT CASE
    WHEN total_count = 0 THEN 0
    ELSE ROUND(null_count::numeric / total_count, 4)
  END AS null_rate
) rates
ORDER BY null_rate DESC, field_name;
