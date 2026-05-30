# 项目路线图

## Milestone 1: 指标 SQL 与基础模型

- 建立 `github_event` 明细表。
- 补充常用索引。
- 完成首批核心指标 SQL。
- 明确时间窗口与时区口径。

## Milestone 2: 数据采集与入库

- 实现按小时下载 GitHub Archive 文件。
- 实现采集状态表，支持断点续采。
- 解析通用事件字段并写入 PostgreSQL。
- 加入重复数据处理，保证 `id` 幂等。

## Milestone 3: ETL 与数据质量

- 增加 raw/staging 表，保留原始事件。
- 增加字段校验、异常记录和采集延迟监控。
- 针对 PushEvent、WatchEvent、ForkEvent、IssuesEvent、PullRequestEvent 做重点字段抽取。

## Milestone 4: 报表与展示

- 建设指标 API 或 BI 数据集。
- 展示核心 KPI、排行榜、事件流和趋势图。
- 支持按语言、事件类型、仓库、开发者筛选。

## Milestone 5: 项目包装

- 完善 README、架构图、数据字典和运行指南。
- 增加 Docker Compose 一键运行。
- 准备 GitHub 项目截图与示例报表。
- 编写项目经历描述，突出数据工程、实时分析和指标体系能力。

