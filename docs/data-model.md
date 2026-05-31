# 数据模型

## 现有明细表

`dataset_github_event.github_event` 是首版 DWD 事件事实表。它抽取了 GitHub 事件的通用字段和部分高价值字段。

| 字段 | 含义 |
| --- | --- |
| `id` | GitHub 事件 ID |
| `actor_id` | 行为人 ID |
| `actor_login` | 行为人登录名 |
| `repo_id` | 仓库 ID |
| `repo_name` | 仓库全名，例如 `owner/repo` |
| `org_id` | 组织 ID |
| `org_login` | 组织登录名 |
| `type` | 事件类型，例如 `PushEvent`、`WatchEvent` |
| `created_at` | 事件发生时间 |
| `action` | 事件动作，例如 `started`、`opened`、`closed` |
| `commit_id` | commit SHA，主要来自 PushEvent |
| `member_id` | 成员 ID，主要来自 MemberEvent |
| `language` | 仓库语言，若源数据缺失可后续补齐 |

## 原始事件表

`dataset_github_event.github_event_raw` 保存 GitHub Archive 原始事件 JSON，用于历史重放、补充新字段和排查解析问题。

| 字段 | 含义 |
| --- | --- |
| `id` | GitHub 事件 ID |
| `archive_hour` | 事件来源的 GitHub Archive 小时文件 |
| `type` | 事件类型 |
| `created_at` | 事件发生时间 |
| `raw_event` | 清洗 NUL 字符后的完整原始事件 JSON |
| `ingested_at` | 入库时间 |

## 采集日志表

`dataset_github_event.github_archive_ingest_log` 记录每个小时文件的采集状态。

| 字段 | 含义 |
| --- | --- |
| `archive_hour` | 采集小时 |
| `archive_url` | GitHub Archive 文件地址 |
| `status` | `running`、`success` 或 `failed` |
| `event_count` | 文件内解析到的事件数 |
| `inserted_count` | 本次新增到明细表的事件数 |
| `raw_inserted_count` | 本次新增到 raw 表的事件数 |
| `error_message` | 失败原因 |
| `started_at` | 采集开始时间 |
| `finished_at` | 采集结束时间 |

## 建议补充字段

为了支撑更完整的分析，后续建议增加以下字段或扩展表：

- `ingested_at timestamptz`：入库时间，用于监控延迟。
- `event_hour timestamptz`：按小时聚合的分区键。
- `repo_owner text`：从 `repo_name` 拆分得到。
- `is_org_repo boolean`：是否组织仓库。

## 推荐索引

```sql
CREATE INDEX IF NOT EXISTS idx_github_event_created_at
ON dataset_github_event.github_event (created_at DESC);

CREATE INDEX IF NOT EXISTS idx_github_event_type_created_at
ON dataset_github_event.github_event (type, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_github_event_repo_created_at
ON dataset_github_event.github_event (repo_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_github_event_actor_created_at
ON dataset_github_event.github_event (actor_id, created_at DESC);
```

## 后续主题模型

- 项目主题：项目活跃度、星标增长、Fork 增长、Issue/PR 活跃度。
- 开发者主题：开发者活跃度、贡献事件分布、参与项目数。
- 语言主题：不同语言事件趋势、热门语言排行。
- 组织主题：组织活跃项目、组织开发者参与度。
- 事件主题：事件类型分布、小时趋势、异常波动。
