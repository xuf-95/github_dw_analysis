# 事件类型解析

本项目优先解析 GitHub Archive 中对项目活跃度和开发者行为分析价值最高的 5 类事件。

## PushEvent

写入表：`dataset_github_event.github_push_event_detail`

关键字段：

- `push_id`
- `ref`
- `head`
- `before`
- `commit_count`
- `distinct_commit_count`
- `commit_shas`

用途：项目代码提交活跃度、开发者提交活跃度、仓库 commit 趋势。

## WatchEvent

写入表：`dataset_github_event.github_watch_event_detail`

关键字段：

- `action`

GitHub Archive 中 star 通常表示为 `WatchEvent` 且 `action = 'started'`。

用途：项目 star 增长排行、项目热度分析。

## ForkEvent

写入表：`dataset_github_event.github_fork_event_detail`

关键字段：

- `forkee_id`
- `forkee_full_name`
- `forkee_owner_login`
- `forkee_html_url`

用途：项目 fork 增长排行、项目传播分析。

## IssuesEvent

写入表：`dataset_github_event.github_issues_event_detail`

关键字段：

- `action`
- `issue_id`
- `issue_number`
- `issue_title`
- `issue_state`
- `issue_author_login`
- `comments_count`
- `labels`

用途：Issue 活跃项目、问题打开/关闭趋势、项目协作活跃度。

## PullRequestEvent

写入表：`dataset_github_event.github_pull_request_event_detail`

关键字段：

- `action`
- `pull_request_id`
- `pull_request_number`
- `pull_request_title`
- `pull_request_state`
- `pull_request_author_login`
- `merged`
- `merged_at`
- `additions`
- `deletions`
- `changed_files`
- `commits_count`
- `review_comments_count`
- `requested_reviewers_count`

用途：PR 活跃项目、合并情况、代码变更规模、协作效率分析。

## 回填方式

```bash
make init-db
make backfill-details
```

也可以限制事件类型：

```bash
.venv/bin/python scripts/backfill_event_details.py --event-type PushEvent --event-type PullRequestEvent
```

## 覆盖率检查

```sql
SELECT *
FROM dataset_github_event.v_event_detail_parse_coverage;
```
