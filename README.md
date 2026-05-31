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

## 快速开始

复制本地环境变量示例：

```bash
cp .env.example .env
```

启动 PostgreSQL：

```bash
make up
```

安装 Python 依赖：

```bash
make install
```

该命令会在项目目录下创建 `.venv`，不会安装到全局 Python 环境。

初始化数据表和指标视图：

```bash
make init-db
```

采集最近 1 个已完成小时的 GitHub Archive 事件：

```bash
make ingest-last-hour
```

如果最新小时文件暂未发布，可以用稳定的历史样例验证链路：

```bash
make ingest-sample-hour
```

也可以指定 UTC 小时采集：

```bash
python3 scripts/ingest_github_archive.py --hour 2026-05-31-10
```

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

建表脚本位于 [sql/schema/001_create_github_event.sql](/Users/xpf/Git/github_dw_analysis/sql/schema/001_create_github_event.sql)。

首批 SQL 位于 [sql/metrics/github_event_metrics.sql](/Users/xpf/Git/github_dw_analysis/sql/metrics/github_event_metrics.sql)。

## 文档

- [架构设计](/Users/xpf/Git/github_dw_analysis/docs/architecture.md)
- [数据模型](/Users/xpf/Git/github_dw_analysis/docs/data-model.md)
- [项目路线图](/Users/xpf/Git/github_dw_analysis/docs/roadmap.md)
