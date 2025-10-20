"""
Task Monitor Module
监控滴答清单任务变化，自动捕获任务完成事件并保存历史记录
"""

import os
import json
import time
import sqlite3
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from pathlib import Path

logger = logging.getLogger(__name__)


class TaskDatabase:
    """任务历史数据库管理"""
    
    def __init__(self, db_path: str = None):
        """
        初始化数据库
        
        Args:
            db_path: 数据库文件路径，默认为当前目录下的 task_history.db
        """
        if db_path is None:
            db_path = os.path.join(os.getcwd(), "task_history.db")
        
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """初始化数据库表结构"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 当前任务快照表（存储最新的未完成任务）
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS current_tasks (
                    task_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT,
                    priority INTEGER DEFAULT 0,
                    start_date TEXT,
                    due_date TEXT,
                    created_time TEXT,
                    modified_time TEXT,
                    last_seen TEXT NOT NULL,
                    raw_data TEXT NOT NULL
                )
            ''')
            
            # 已完成任务表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS completed_tasks (
                    task_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT,
                    priority INTEGER DEFAULT 0,
                    start_date TEXT,
                    due_date TEXT,
                    created_time TEXT,
                    completed_time TEXT NOT NULL,
                    completion_detected_at TEXT NOT NULL,
                    raw_data TEXT NOT NULL
                )
            ''')
            
            # 已删除任务表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS deleted_tasks (
                    task_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT,
                    priority INTEGER DEFAULT 0,
                    start_date TEXT,
                    due_date TEXT,
                    created_time TEXT,
                    deleted_detected_at TEXT NOT NULL,
                    raw_data TEXT NOT NULL
                )
            ''')
            
            # 创建索引加速查询
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_completed_time 
                ON completed_tasks(completed_time)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_completion_detected_at 
                ON completed_tasks(completion_detected_at)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_project_completed 
                ON completed_tasks(project_id, completed_time)
            ''')
            
            conn.commit()
            logger.info(f"Database initialized at {self.db_path}")
    
    def update_current_tasks(self, tasks: List[Dict]) -> None:
        """
        更新当前任务快照
        
        Args:
            tasks: 当前所有未完成任务列表
        """
        now = datetime.now().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 获取任务ID集合
            task_ids = {task['id'] for task in tasks}
            
            # 删除数据库中所有当前任务（将在下一步重新插入存在的任务）
            cursor.execute("DELETE FROM current_tasks")
            
            # 插入或更新所有当前任务
            for task in tasks:
                cursor.execute('''
                    INSERT OR REPLACE INTO current_tasks 
                    (task_id, project_id, title, content, priority, start_date, 
                     due_date, created_time, modified_time, last_seen, raw_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    task['id'],
                    task.get('projectId', ''),
                    task.get('title', ''),
                    task.get('content', ''),
                    task.get('priority', 0),
                    task.get('startDate', ''),
                    task.get('dueDate', ''),
                    task.get('createdTime', ''),
                    task.get('modifiedTime', ''),
                    now,
                    json.dumps(task, ensure_ascii=False)
                ))
            
            conn.commit()
            logger.debug(f"Updated {len(tasks)} current tasks")
    
    def get_current_task_ids(self) -> Set[str]:
        """获取当前所有任务的ID集合"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT task_id FROM current_tasks")
            return {row[0] for row in cursor.fetchall()}
    
    def get_previous_task_ids(self) -> Set[str]:
        """获取上一次快照的任务ID集合（在更新前调用）"""
        return self.get_current_task_ids()
    
    def mark_task_as_completed(self, task_id: str, task_data: Dict) -> None:
        """
        标记任务为已完成
        
        Args:
            task_id: 任务ID
            task_data: 任务完整数据
        """
        now = datetime.now().isoformat()
        completed_time = task_data.get('completedTime') or task_data.get('modifiedTime') or now
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 插入到已完成任务表
            cursor.execute('''
                INSERT OR REPLACE INTO completed_tasks 
                (task_id, project_id, title, content, priority, start_date, 
                 due_date, created_time, completed_time, completion_detected_at, raw_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                task_id,
                task_data.get('projectId', ''),
                task_data.get('title', ''),
                task_data.get('content', ''),
                task_data.get('priority', 0),
                task_data.get('startDate', ''),
                task_data.get('dueDate', ''),
                task_data.get('createdTime', ''),
                completed_time,
                now,
                json.dumps(task_data, ensure_ascii=False)
            ))
            
            # 从当前任务表中删除
            cursor.execute("DELETE FROM current_tasks WHERE task_id = ?", (task_id,))
            
            conn.commit()
            logger.info(f"Marked task {task_id} ({task_data.get('title')}) as completed")
    
    def mark_task_as_deleted(self, task_id: str, task_data: Dict) -> None:
        """
        标记任务为已删除
        
        Args:
            task_id: 任务ID
            task_data: 任务数据（从上一次快照获取）
        """
        now = datetime.now().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 插入到已删除任务表
            cursor.execute('''
                INSERT OR REPLACE INTO deleted_tasks 
                (task_id, project_id, title, content, priority, start_date, 
                 due_date, created_time, deleted_detected_at, raw_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                task_id,
                task_data.get('projectId', ''),
                task_data.get('title', ''),
                task_data.get('content', ''),
                task_data.get('priority', 0),
                task_data.get('startDate', ''),
                task_data.get('dueDate', ''),
                task_data.get('createdTime', ''),
                now,
                json.dumps(task_data, ensure_ascii=False)
            ))
            
            # 从当前任务表中删除
            cursor.execute("DELETE FROM current_tasks WHERE task_id = ?", (task_id,))
            
            conn.commit()
            logger.info(f"Marked task {task_id} ({task_data.get('title')}) as deleted")
    
    def get_task_data(self, task_id: str) -> Optional[Dict]:
        """
        从当前任务表获取任务数据
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务数据字典，如果不存在返回None
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT raw_data FROM current_tasks WHERE task_id = ?", (task_id,))
            row = cursor.fetchone()
            
            if row:
                return json.loads(row[0])
            return None
    
    def get_completed_tasks(self, start_date: Optional[str] = None, 
                           end_date: Optional[str] = None,
                           project_id: Optional[str] = None,
                           limit: int = None) -> List[Dict]:
        """
        查询已完成任务
        
        Args:
            start_date: 开始日期（ISO格式），按完成时间过滤
            end_date: 结束日期（ISO格式），按完成时间过滤
            project_id: 项目ID过滤
            limit: 返回结果数量限制
            
        Returns:
            已完成任务列表
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM completed_tasks WHERE 1=1"
            params = []
            
            if start_date:
                query += " AND completed_time >= ?"
                params.append(start_date)
            
            if end_date:
                query += " AND completed_time <= ?"
                params.append(end_date)
            
            if project_id:
                query += " AND project_id = ?"
                params.append(project_id)
            
            query += " ORDER BY completed_time DESC"
            
            if limit:
                query += f" LIMIT {limit}"
            
            cursor.execute(query, params)
            
            columns = [desc[0] for desc in cursor.description]
            results = []
            
            for row in cursor.fetchall():
                task_dict = dict(zip(columns, row))
                # 解析raw_data
                task_dict['raw_data'] = json.loads(task_dict['raw_data'])
                results.append(task_dict)
            
            return results
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 当前未完成任务数
            cursor.execute("SELECT COUNT(*) FROM current_tasks")
            current_count = cursor.fetchone()[0]
            
            # 已完成任务数
            cursor.execute("SELECT COUNT(*) FROM completed_tasks")
            completed_count = cursor.fetchone()[0]
            
            # 已删除任务数
            cursor.execute("SELECT COUNT(*) FROM deleted_tasks")
            deleted_count = cursor.fetchone()[0]
            
            # 今天完成的任务数
            today = datetime.now().date().isoformat()
            cursor.execute(
                "SELECT COUNT(*) FROM completed_tasks WHERE DATE(completed_time) = ?",
                (today,)
            )
            completed_today = cursor.fetchone()[0]
            
            # 本周完成的任务数
            week_start = (datetime.now() - timedelta(days=datetime.now().weekday())).date().isoformat()
            cursor.execute(
                "SELECT COUNT(*) FROM completed_tasks WHERE completed_time >= ?",
                (week_start,)
            )
            completed_this_week = cursor.fetchone()[0]
            
            return {
                "current_tasks": current_count,
                "completed_tasks": completed_count,
                "deleted_tasks": deleted_count,
                "completed_today": completed_today,
                "completed_this_week": completed_this_week
            }


class TaskMonitor:
    """任务监控器 - 定期检查任务变化"""
    
    def __init__(self, ticktick_client, db_path: str = None, 
                 check_interval: int = 600):
        """
        初始化任务监控器
        
        Args:
            ticktick_client: TickTick客户端实例
            db_path: 数据库文件路径
            check_interval: 检查间隔（秒），默认600秒（10分钟）
        """
        self.client = ticktick_client
        self.database = TaskDatabase(db_path)
        self.check_interval = check_interval
        self._running = False
        self._thread = None
        
        logger.info(f"TaskMonitor initialized with check_interval={check_interval}s")
    
    def start(self):
        """启动监控（后台线程）"""
        if self._running:
            logger.warning("TaskMonitor is already running")
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        logger.info("TaskMonitor started")
    
    def stop(self):
        """停止监控"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("TaskMonitor stopped")
    
    def _monitor_loop(self):
        """监控循环（在后台线程中运行）"""
        # 启动时立即执行一次检查
        self.check_tasks()
        
        while self._running:
            try:
                time.sleep(self.check_interval)
                if self._running:
                    self.check_tasks()
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}", exc_info=True)
    
    def check_tasks(self):
        """
        执行一次任务检查
        
        检查流程：
        1. 获取上一次的任务ID集合
        2. 获取当前所有未完成任务
        3. 对比找出消失的任务
        4. 对每个消失的任务，尝试获取详情判断是完成还是删除
        5. 更新当前任务快照
        """
        try:
            logger.info("Starting task check...")
            start_time = time.time()
            
            # 1. 获取上一次的任务ID集合
            previous_task_ids = self.database.get_previous_task_ids()
            logger.debug(f"Previous task count: {len(previous_task_ids)}")
            
            # 2. 获取所有项目
            projects = self.client.get_projects()
            if isinstance(projects, dict) and 'error' in projects:
                logger.error(f"Failed to get projects: {projects['error']}")
                return
            
            # 3. 遍历所有项目获取未完成任务
            current_tasks = []
            current_task_ids = set()
            
            for project in projects:
                if project.get('closed'):
                    continue  # 跳过已关闭的项目
                
                project_id = project.get('id')
                try:
                    project_data = self.client.get_project_with_data(project_id)
                    
                    if isinstance(project_data, dict) and 'tasks' in project_data:
                        tasks = project_data['tasks']
                        for task in tasks:
                            current_tasks.append(task)
                            current_task_ids.add(task['id'])
                except Exception as e:
                    logger.error(f"Error fetching tasks for project {project_id}: {e}")
            
            logger.debug(f"Current task count: {len(current_tasks)}")
            
            # 4. 找出消失的任务
            disappeared_task_ids = previous_task_ids - current_task_ids
            
            if disappeared_task_ids:
                logger.info(f"Found {len(disappeared_task_ids)} disappeared tasks")
                
                # 5. 检查每个消失的任务
                for task_id in disappeared_task_ids:
                    task_data = self.database.get_task_data(task_id)
                    
                    if not task_data:
                        logger.warning(f"Task {task_id} data not found in database")
                        continue
                    
                    project_id = task_data.get('projectId')
                    
                    try:
                        # 尝试获取任务详情
                        task_detail = self.client.get_task(project_id, task_id)
                        
                        if isinstance(task_detail, dict) and 'error' not in task_detail:
                            # 任务仍然存在，检查是否完成
                            # 根据TickTick API，status=2表示已完成
                            if task_detail.get('status') == 2:
                                # 任务已完成
                                self.database.mark_task_as_completed(task_id, task_detail)
                            else:
                                # 任务存在但未完成？可能是API延迟，先不处理
                                logger.warning(f"Task {task_id} exists but status is not completed")
                        else:
                            # 任务不存在，标记为已删除
                            self.database.mark_task_as_deleted(task_id, task_data)
                    
                    except Exception as e:
                        logger.error(f"Error checking task {task_id}: {e}")
                        # 如果无法获取任务详情，假定为已删除
                        self.database.mark_task_as_deleted(task_id, task_data)
            
            # 6. 更新当前任务快照
            self.database.update_current_tasks(current_tasks)
            
            elapsed = time.time() - start_time
            logger.info(f"Task check completed in {elapsed:.2f}s")
            
        except Exception as e:
            logger.error(f"Error in check_tasks: {e}", exc_info=True)

