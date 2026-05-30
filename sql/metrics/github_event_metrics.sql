-- Core metrics for dataset_github_event.github_event.
-- Timezone policy: dashboard "today" uses Asia/Shanghai.

CREATE SCHEMA IF NOT EXISTS dataset_github_event;

-- 1. 今日开发者和项目总数
CREATE OR REPLACE VIEW dataset_github_event.v_today_actor_repo_summary AS
WITH params AS (
  SELECT date_trunc('day', now() AT TIME ZONE 'Asia/Shanghai') AT TIME ZONE 'Asia/Shanghai' AS day_start
)
SELECT
  COUNT(DISTINCT actor_id) FILTER (WHERE actor_id IS NOT NULL) AS today_developer_count,
  COUNT(DISTINCT repo_id) FILTER (WHERE repo_id IS NOT NULL) AS today_repo_count
FROM dataset_github_event.github_event e
CROSS JOIN params p
WHERE e.created_at >= p.day_start;

-- 2. 过去24小时最活跃项目
CREATE OR REPLACE VIEW dataset_github_event.v_top_active_repos_24h AS
SELECT
  repo_id,
  repo_name,
  COUNT(*) AS event_count,
  COUNT(DISTINCT actor_id) FILTER (WHERE actor_id IS NOT NULL) AS active_developer_count,
  MAX(created_at) AS latest_event_at
FROM dataset_github_event.github_event
WHERE created_at >= now() - INTERVAL '24 hours'
  AND repo_id IS NOT NULL
GROUP BY repo_id, repo_name
ORDER BY event_count DESC, active_developer_count DESC, latest_event_at DESC
LIMIT 100;

-- 3. 过去24小时最活跃开发者
CREATE OR REPLACE VIEW dataset_github_event.v_top_active_developers_24h AS
SELECT
  actor_id,
  actor_login,
  COUNT(*) AS event_count,
  COUNT(DISTINCT repo_id) FILTER (WHERE repo_id IS NOT NULL) AS touched_repo_count,
  MAX(created_at) AS latest_event_at
FROM dataset_github_event.github_event
WHERE created_at >= now() - INTERVAL '24 hours'
  AND actor_id IS NOT NULL
GROUP BY actor_id, actor_login
ORDER BY event_count DESC, touched_repo_count DESC, latest_event_at DESC
LIMIT 100;

-- 4. 今日公开事件总数
CREATE OR REPLACE VIEW dataset_github_event.v_today_event_summary AS
WITH params AS (
  SELECT date_trunc('day', now() AT TIME ZONE 'Asia/Shanghai') AT TIME ZONE 'Asia/Shanghai' AS day_start
)
SELECT
  COUNT(*) AS today_event_count,
  MIN(created_at) AS first_event_at,
  MAX(created_at) AS latest_event_at
FROM dataset_github_event.github_event e
CROSS JOIN params p
WHERE e.created_at >= p.day_start;

-- 5. 过去24小时星标项目排行
-- GitHub Archive uses WatchEvent with action = 'started' for star events.
CREATE OR REPLACE VIEW dataset_github_event.v_top_starred_repos_24h AS
SELECT
  repo_id,
  repo_name,
  COUNT(*) AS star_count,
  COUNT(DISTINCT actor_id) FILTER (WHERE actor_id IS NOT NULL) AS starring_developer_count,
  MAX(created_at) AS latest_star_at
FROM dataset_github_event.github_event
WHERE created_at >= now() - INTERVAL '24 hours'
  AND type = 'WatchEvent'
  AND action = 'started'
  AND repo_id IS NOT NULL
GROUP BY repo_id, repo_name
ORDER BY star_count DESC, latest_star_at DESC
LIMIT 100;

-- 6. 实时事件展示
CREATE OR REPLACE VIEW dataset_github_event.v_latest_events AS
SELECT
  id,
  type,
  action,
  actor_id,
  actor_login,
  repo_id,
  repo_name,
  org_id,
  org_login,
  language,
  created_at
FROM dataset_github_event.github_event
ORDER BY created_at DESC, id DESC
LIMIT 200;

-- Optional: event distribution for dashboard filters.
CREATE OR REPLACE VIEW dataset_github_event.v_event_type_distribution_24h AS
SELECT
  type,
  COUNT(*) AS event_count,
  COUNT(DISTINCT actor_id) FILTER (WHERE actor_id IS NOT NULL) AS developer_count,
  COUNT(DISTINCT repo_id) FILTER (WHERE repo_id IS NOT NULL) AS repo_count
FROM dataset_github_event.github_event
WHERE created_at >= now() - INTERVAL '24 hours'
GROUP BY type
ORDER BY event_count DESC;

-- Optional: hourly trend for the last 24 hours.
CREATE OR REPLACE VIEW dataset_github_event.v_event_hourly_trend_24h AS
SELECT
  date_trunc('hour', created_at) AS event_hour,
  COUNT(*) AS event_count,
  COUNT(DISTINCT actor_id) FILTER (WHERE actor_id IS NOT NULL) AS developer_count,
  COUNT(DISTINCT repo_id) FILTER (WHERE repo_id IS NOT NULL) AS repo_count
FROM dataset_github_event.github_event
WHERE created_at >= now() - INTERVAL '24 hours'
GROUP BY date_trunc('hour', created_at)
ORDER BY event_hour;

