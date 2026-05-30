# github_dw_analysis

基于 GitHub Archive 公开数据集，构建 GitHub 事件数据的近实时采集、清洗、指标计算与报表展示项目。

项目目标是把 GitHub 中的项目、开发者、组织与 20 多种事件类型沉淀成可分析的数据资产，并围绕实时活跃度、开源趋势、项目增长、开发者行为等方向建设指标与报表。

## 核心能力

- 采集 GitHub Archive 小时级事件数据。
- 解析 PushEvent、WatchEvent、ForkEvent、IssuesEvent、PullRequestEvent 等事件。
- 建设 ODS、DWD、DWS、ADS 分层数据模型。
- 计算今日开发者/项目数、24 小时活跃项目、24 小时活跃开发者、今日事件数、星标排行、实时事件流等指标。
- 支持后续接入可视化报表，例如 Metabase、Superset、Grafana 或自研前端。

## 推荐技术栈

首版建议采用低复杂度、容易在个人项目中展示的组合：

- 数据源：GitHub Archive hourly JSON gzip files
- 采集与 ETL：Python
- 存储与分析：PostgreSQL
- 调度：cron 或 APScheduler；后续可升级 Airflow
- 可视化：Metabase / Apache Superset / Streamlit / 自研 React Dashboard
- 部署：Docker Compose

## 当前数据表

```sql
CREATE TABLE dataset_github_event.github_event (
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
```

## 首批指标

- 今日开发者和项目总数
- 过去 24 小时最活跃项目
- 过去 24 小时最活跃开发者
- 今日公开事件总数
- 过去 24 小时星标项目排行
- 实时事件展示

建表脚本位于 [sql/schema/001_create_github_event.sql](/Users/xpf/Documents/Github实时数据同步与分析/sql/schema/001_create_github_event.sql)。

首批 SQL 位于 [sql/metrics/github_event_metrics.sql](/Users/xpf/Documents/Github实时数据同步与分析/sql/metrics/github_event_metrics.sql)。

## 文档

- [架构设计](/Users/xpf/Documents/Github实时数据同步与分析/docs/architecture.md)
- [数据模型](/Users/xpf/Documents/Github实时数据同步与分析/docs/data-model.md)
- [项目路线图](/Users/xpf/Documents/Github实时数据同步与分析/docs/roadmap.md)
