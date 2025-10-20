# 任务监控配置说明

## 环境变量配置

在你的 `.env` 文件中，可以添加以下配置：

### 基础配置

```env
# TickTick OAuth Credentials
TICKTICK_CLIENT_ID=your_client_id_here
TICKTICK_CLIENT_SECRET=your_client_secret_here
TICKTICK_ACCESS_TOKEN=your_access_token
TICKTICK_REFRESH_TOKEN=your_refresh_token
```

### 任务监控配置（新功能）

```env
# 任务检查间隔（秒）
# 默认值：600（10分钟）
# 这个参数控制后台监控器多久检查一次任务变化
TASK_MONITOR_INTERVAL=600

# 自定义数据库路径（可选）
# 如果不设置，将在当前目录下创建 task_history.db
# TASK_MONITOR_DB_PATH=/path/to/custom/task_history.db
```

### 滴答清单（Dida365）配置

如果你使用的是中国版滴答清单（Dida365），需要添加：

```env
TICKTICK_BASE_URL=https://api.dida365.com/open/v1
TICKTICK_AUTH_URL=https://dida365.com/oauth/authorize
TICKTICK_TOKEN_URL=https://dida365.com/oauth/token
```

## 任务监控功能说明

### 工作原理

1. **后台监控**：服务器启动后，会自动启动一个后台线程，每隔 `TASK_MONITOR_INTERVAL` 秒检查一次所有任务
2. **任务快照**：每次检查时，会保存当前所有未完成任务的快照
3. **变化检测**：通过对比两次快照，识别哪些任务消失了
4. **状态判断**：对于消失的任务，通过API查询判断是已完成还是已删除
5. **历史保存**：将已完成的任务保存到数据库中，支持按时间过滤查询

### 数据库结构

任务监控器使用SQLite数据库存储三张表：

- `current_tasks`：当前未完成任务快照
- `completed_tasks`：已完成任务历史
- `deleted_tasks`：已删除任务历史

### 新增的MCP工具

1. **get_completed_tasks**: 查询已完成任务
   - 支持按日期范围过滤
   - 支持按项目过滤
   - 支持限制返回数量

2. **get_task_statistics**: 获取任务统计信息
   - 当前任务数
   - 已完成任务总数
   - 今天完成的任务数
   - 本周完成的任务数
   - 完成率

3. **trigger_task_check**: 手动触发任务检查
   - 不等待定时检查，立即更新任务历史

### 使用示例

```python
# 查询所有已完成任务
await get_completed_tasks()

# 查询今天完成的任务
await get_completed_tasks(start_date="2025-10-20")

# 查询10月份完成的任务
await get_completed_tasks(start_date="2025-10-01", end_date="2025-10-31")

# 查询特定项目的已完成任务
await get_completed_tasks(project_id="project_id_here")

# 获取统计信息
await get_task_statistics()

# 手动触发检查
await trigger_task_check()
```

## 性能考虑

- **检查间隔**：默认10分钟是一个平衡值，既能及时捕获任务完成，又不会过度消耗API配额
- **API调用**：每次检查会遍历所有项目，根据项目数量可能需要多次API调用
- **数据库大小**：随着时间推移，数据库会不断增长。可以定期清理旧数据或备份

## 注意事项

1. 任务监控器在服务器启动时自动启动
2. 第一次检查会保存当前所有任务作为基准，不会报告任何完成的任务
3. 如果服务器长时间关闭，重启后可能会错过一些任务完成事件
4. 删除的任务无法区分是用户主动删除还是系统清理，都会被记录为"已删除"

