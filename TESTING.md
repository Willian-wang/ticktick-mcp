# 任务监控功能测试指南

## 测试前准备

1. 确保已经完成TickTick OAuth认证
2. 在 `.env` 文件中配置监控间隔（可选）：
   ```env
   TASK_MONITOR_INTERVAL=60  # 设置为60秒以便快速测试
   ```

## 测试步骤

### 1. 启动MCP服务器

```bash
cd c:\Users\Jayfeather\code\willian-ticktick-mcp
uv run -m ticktick_mcp.cli run
```

服务器启动时应该看到类似以下日志：
```
INFO:__main__:TickTick client initialized successfully
INFO:__main__:Successfully connected to TickTick API with X projects
INFO:__main__:Task monitor started with check interval: 60s
INFO:root:TaskMonitor initialized with check_interval=60s
INFO:root:Database initialized at task_history.db
INFO:root:TaskMonitor started
INFO:root:Starting task check...
```

### 2. 在Claude中测试基础功能

连接Claude Desktop后，尝试以下命令：

```
# 查看当前任务统计
get_task_statistics()

# 应该显示：
# 📊 Task Statistics
# 📝 Current Tasks: X
# ✅ Total Completed: 0  (第一次运行为0)
# 🎯 Completed Today: 0
# ...
```

### 3. 测试任务完成捕获

**步骤A：创建测试任务**

在Claude中：
```
# 创建一个测试任务
create_task(title="测试任务监控功能", project_id="your_project_id", priority=5)
```

**步骤B：完成任务**

在TickTick应用或网页端完成这个任务

**步骤C：手动触发检查**

在Claude中：
```
# 不等待自动检查，立即触发
trigger_task_check()
```

应该看到：
```
✅ Task check completed successfully. The task history has been updated.
```

**步骤D：查询已完成任务**

```
# 查询所有已完成任务
get_completed_tasks()

# 应该能看到刚才完成的任务
```

### 4. 测试时间过滤

```
# 查询今天完成的任务
get_completed_tasks(start_date="2025-10-20")

# 查询特定时间范围
get_completed_tasks(start_date="2025-10-01", end_date="2025-10-31")

# 限制返回数量
get_completed_tasks(limit=10)
```

### 5. 测试项目过滤

```
# 查询特定项目的已完成任务
get_completed_tasks(project_id="your_project_id")
```

### 6. 测试统计功能

```
# 完成几个任务后再次查看统计
get_task_statistics()

# 应该看到数字增加：
# 📊 Task Statistics
# 📝 Current Tasks: X
# ✅ Total Completed: Y  (增加了)
# 🎯 Completed Today: Z
# 📅 Completed This Week: W
# 🗑️ Deleted Tasks: 0
# 📈 Completion Rate: XX.X%
```

### 7. 测试自动监控

不手动触发，等待配置的时间间隔（例如60秒），在此期间：
1. 在TickTick中完成一个任务
2. 等待监控自动运行
3. 查看服务器日志应该显示类似：
   ```
   INFO:root:Starting task check...
   INFO:root:Found 1 disappeared tasks
   INFO:root:Marked task xxx (任务标题) as completed
   INFO:root:Task check completed in X.XXs
   ```
4. 在Claude中查询已完成任务，应该能看到自动捕获的任务

### 8. 检查数据库

可以直接查看SQLite数据库：

```bash
# 使用sqlite3命令行工具
sqlite3 task_history.db

# 查询已完成任务表
SELECT title, completed_time FROM completed_tasks ORDER BY completed_time DESC;

# 查看表结构
.schema completed_tasks

# 退出
.exit
```

## 验证清单

- [ ] 服务器启动时TaskMonitor成功初始化
- [ ] 数据库文件 `task_history.db` 被创建
- [ ] 第一次检查建立基线（不报告任何完成）
- [ ] 手动触发检查工作正常
- [ ] 完成的任务被正确捕获
- [ ] `get_completed_tasks` 能返回已完成任务
- [ ] 时间过滤工作正常
- [ ] 项目过滤工作正常
- [ ] `get_task_statistics` 显示正确的统计数据
- [ ] 自动定期检查在后台正常运行
- [ ] 已删除的任务被正确识别

## 常见问题

### Q: 为什么第一次运行没有显示任何已完成任务？

A: 第一次检查会建立基线，只保存当前任务状态。只有在后续检查中才能检测到任务的变化。

### Q: 如何验证监控正在运行？

A: 查看服务器日志，应该每隔配置的间隔时间看到 "Starting task check..." 和 "Task check completed" 的日志。

### Q: 任务完成后没有被捕获怎么办？

A: 
1. 确认任务确实从未完成列表中消失
2. 检查API是否返回了任务状态（status=2表示已完成）
3. 如果任务是在服务器启动前完成的，无法被捕获
4. 手动触发 `trigger_task_check()` 来立即检查

### Q: 数据库文件在哪里？

A: 默认在服务器运行目录下创建 `task_history.db`。可以通过环境变量 `TASK_MONITOR_DB_PATH` 自定义路径。

### Q: 如何清空历史数据？

A: 停止服务器，删除 `task_history.db` 文件，然后重新启动服务器。

## 性能测试

对于有大量任务的用户，建议测试：

1. **检查耗时**：查看日志中 "Task check completed in X.XXs" 的时间
2. **内存使用**：监控服务器进程的内存占用
3. **数据库大小**：随着时间推移观察 `task_history.db` 的文件大小
4. **API配额**：注意TickTick API的调用频率限制

建议：
- 如果有超过50个项目，考虑增加检查间隔到15-30分钟
- 定期备份数据库文件
- 考虑定期清理旧的历史数据

## 调试建议

如果遇到问题，可以：

1. 设置更详细的日志级别
2. 查看完整的服务器日志输出
3. 直接查询SQLite数据库验证数据
4. 减小检查间隔以便更快重现问题
5. 查看 `task_monitor.py` 中的详细错误日志

