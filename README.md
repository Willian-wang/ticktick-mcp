# TickTick MCP Server

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server for TickTick that enables interacting with your TickTick task management system directly through Claude and other MCP clients.

## Features

- 📋 View all your TickTick projects and tasks
- ✏️ Create new projects and tasks through natural language
- 🔄 Update existing task details (title, content, dates, priority)
- ✅ Mark tasks as complete
- 🗑️ Delete tasks and projects
- 🔄 Full integration with TickTick's open API
- 🔌 Seamless integration with Claude and other MCP clients
- 📊 **NEW**: Automatic task completion tracking with background monitoring
- 🗄️ **NEW**: Query completed tasks history with time-based filtering
- 📈 **NEW**: Task statistics and completion analytics

## Prerequisites

- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) - Fast Python package installer and resolver
- TickTick account with API access
- TickTick API credentials (Client ID, Client Secret, Access Token)

## Installation

1. **Clone this repository**:
   ```bash
   git clone https://github.com/jacepark12/ticktick-mcp.git
   cd ticktick-mcp
   ```

2. **Install with uv**:
   ```bash
   # Install uv if you don't have it already
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Create a virtual environment
   uv venv

   # Activate the virtual environment
   # On macOS/Linux:
   source .venv/bin/activate
   # On Windows:
   .venv\Scripts\activate

   # Install the package
   uv pip install -e .
   ```

3. **Authenticate with TickTick**:
   ```bash
   # Run the authentication flow
   uv run -m ticktick_mcp.cli auth
   ```

   This will:
   - Ask for your TickTick Client ID and Client Secret
   - Open a browser window for you to log in to TickTick
   - Automatically save your access tokens to a `.env` file

4. **Test your configuration**:
   ```bash
   uv run test_server.py
   ```
   This will verify that your TickTick credentials are working correctly.

## Authentication with TickTick

This server uses OAuth2 to authenticate with TickTick. The setup process is straightforward:

1. Register your application at the [TickTick Developer Center](https://developer.ticktick.com/manage)
   - Set the redirect URI to `http://localhost:8000/callback`
   - Note your Client ID and Client Secret

2. Run the authentication command:
   ```bash
   uv run -m ticktick_mcp.cli auth
   ```

3. Follow the prompts to enter your Client ID and Client Secret

4. A browser window will open for you to authorize the application with your TickTick account

5. After authorizing, you'll be redirected back to the application, and your access tokens will be automatically saved to the `.env` file

The server handles token refresh automatically, so you won't need to reauthenticate unless you revoke access or delete your `.env` file.

## Authentication with Dida365

[滴答清单 - Dida365](https://dida365.com/home) is China version of TickTick, and the authentication process is similar to TickTick. Follow these steps to set up Dida365 authentication:

1. Register your application at the [Dida365 Developer Center](https://developer.dida365.com/manage)
   - Set the redirect URI to `http://localhost:8000/callback`
   - Note your Client ID and Client Secret

2. Add environment variables to your `.env` file:
   ```env
   TICKTICK_BASE_URL='https://api.dida365.com/open/v1'
   TICKTICK_AUTH_URL='https://dida365.com/oauth/authorize'
   TICKTICK_TOKEN_URL='https://dida365.com/oauth/token'
   ```

3. Follow the same authentication steps as for TickTick

## Usage with Claude for Desktop

1. Install [Claude for Desktop](https://claude.ai/download)
2. Edit your Claude for Desktop configuration file:

   **macOS**:
   ```bash
   nano ~/Library/Application\ Support/Claude/claude_desktop_config.json
   ```

   **Windows**:
   ```bash
   notepad %APPDATA%\Claude\claude_desktop_config.json
   ```

3. Add the TickTick MCP server configuration, using absolute paths:
   ```json
   {
      "mcpServers": {
         "ticktick": {
            "command": "<absolute path to uv>",
            "args": ["run", "--directory", "<absolute path to ticktick-mcp directory>", "-m", "ticktick_mcp.cli", "run"]
         }
      }
   }
   ```

4. Restart Claude for Desktop

Once connected, you'll see the TickTick MCP server tools available in Claude, indicated by the 🔨 (tools) icon.

## Available MCP Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_projects` | List all your TickTick projects | None |
| `get_project` | Get details about a specific project | `project_id` |
| `get_project_tasks` | List all tasks in a project | `project_id` |
| `get_task` | Get details about a specific task | `project_id`, `task_id` |
| `create_task` | Create a new task | `title`, `project_id`, `content` (optional), `start_date` (optional), `due_date` (optional), `priority` (optional) |
| `update_task` | Update an existing task | `task_id`, `project_id`, `title` (optional), `content` (optional), `start_date` (optional), `due_date` (optional), `priority` (optional) |
| `complete_task` | Mark a task as complete | `project_id`, `task_id` |
| `delete_task` | Delete a task | `project_id`, `task_id` |
| `create_project` | Create a new project | `name`, `color` (optional), `view_mode` (optional) |
| `delete_project` | Delete a project | `project_id` |

## Task-specific MCP Tools

### Task Retrieval & Search
| Tool | Description | Parameters |
|------|-------------|------------|
| `get_all_tasks` | Get all tasks from all projects | None |
| `get_tasks_by_priority` | Get tasks filtered by priority level | `priority_id` (0: None, 1: Low, 3: Medium, 5: High) |
| `search_tasks` | Search tasks by title, content, or subtasks | `search_term` |

### Date-Based Task Retrieval
| Tool | Description | Parameters |
|------|-------------|------------|
| `get_tasks_due_today` | Get all tasks due today | None |
| `get_tasks_due_tomorrow` | Get all tasks due tomorrow | None |
| `get_tasks_due_in_days` | Get tasks due in exactly X days | `days` (0 = today, 1 = tomorrow, etc.) |
| `get_tasks_due_this_week` | Get tasks due within the next 7 days | None |
| `get_overdue_tasks` | Get all overdue tasks | None |

### Getting Things Done (GTD) Framework
| Tool | Description | Parameters |
|------|-------------|------------|
| `get_engaged_tasks` | Get "engaged" tasks (high priority or overdue) | None |
| `get_next_tasks` | Get "next" tasks (medium priority or due tomorrow) | None |
| `batch_create_tasks` | Create multiple tasks at once | `tasks` (list of task dictionaries) |

### Task History & Monitoring (NEW)
| Tool | Description | Parameters |
|------|-------------|------------|
| `get_completed_tasks` | Query completed tasks with time filtering | `start_date` (optional), `end_date` (optional), `project_id` (optional), `limit` (optional, default: 50) |
| `get_task_statistics` | Get task statistics and completion analytics | None |
| `trigger_task_check` | Manually trigger task check to update history | None |

## Example Prompts for Claude

Here are some example prompts to use with Claude after connecting the TickTick MCP server:

### General

- "Show me all my TickTick projects"
- "Create a new task called 'Finish MCP server documentation' in my work project with high priority"
- "List all tasks in my personal project"
- "Mark the task 'Buy groceries' as complete"
- "Create a new project called 'Vacation Planning' with a blue color"
- "When is my next deadline in TickTick?"

### Task Filtering Queries

- "What tasks do I have due today?"
- "Show me everything that's overdue"
- "Show me all tasks due this week"
- "Search for tasks about 'project alpha'"
- "Show me all tasks with 'client' in the title or description"
- "Show me all my high priority tasks"

### GTD Workflow

Following David Allen's "Getting Things Done" framework, manage an Engaged and Next actions.

- Engaged will retrieve tasks of high priority, due today or overdue.
- Next will retrieve medium priority or due tomorrow.
- Break down complex actions into smaller actions with batch_creation

For example:

- "Time block the rest of my day from 2-8pm with items from my engaged list"
- "Walk me through my next actions and help my identify what I should focus on tomorrow?" 
- "Break down this project into 5 smaller actionable tasks"

### Task History & Analytics (NEW)

- "Show me all tasks I completed today"
- "What tasks did I complete this week?"
- "Show me my task completion statistics"
- "What did I accomplish in October?"
- "How many tasks have I completed in the Work project?"
- "Update my task history now" (manually trigger check)

## Task Monitoring Feature

### Overview

The MCP server now includes an automatic task monitoring system that tracks task completions in the background. This solves a key limitation of the TickTick Open API, which doesn't provide a direct way to query completed tasks.

### How It Works

1. **Background Monitoring**: When the server starts, a background thread begins monitoring your tasks at regular intervals (default: 10 minutes)
2. **Task Snapshots**: Each check saves a snapshot of all current incomplete tasks
3. **Change Detection**: By comparing snapshots, the system detects which tasks have disappeared (completed or deleted)
4. **Status Verification**: For disappeared tasks, the system queries the API to determine if they were completed or deleted
5. **History Storage**: Completed tasks are saved to a local SQLite database with full metadata and timestamps
6. **Time-Based Queries**: You can query completed tasks by date range, project, or other criteria

### Configuration

Add these environment variables to your `.env` file:

```env
# Check interval in seconds (default: 600 = 10 minutes)
TASK_MONITOR_INTERVAL=600

# Optional: Custom database path
# TASK_MONITOR_DB_PATH=/path/to/custom/task_history.db
```

See [CONFIG.md](CONFIG.md) for detailed configuration options.

### Database

The monitoring system uses SQLite to store three tables:
- `current_tasks`: Snapshot of current incomplete tasks
- `completed_tasks`: History of completed tasks (queryable)
- `deleted_tasks`: History of deleted tasks

The database file (`task_history.db`) is created automatically in the server's working directory.

### Important Notes

- The first check after starting the server establishes a baseline and won't report any completions
- If the server is offline, task completions during that time won't be captured
- The monitoring runs continuously as long as the server is running
- You can manually trigger a check at any time using the `trigger_task_check` tool

## Development

### Project Structure

```
ticktick-mcp/
├── .env.template          # Template for environment variables
├── CONFIG.md              # Configuration guide for task monitoring
├── README.md              # Project documentation
├── requirements.txt       # Project dependencies
├── setup.py               # Package setup file
├── test_server.py         # Test script for server configuration
├── task_history.db        # SQLite database (created at runtime)
└── ticktick_mcp/          # Main package
    ├── __init__.py        # Package initialization
    ├── authenticate.py    # OAuth authentication utility
    ├── cli.py             # Command-line interface
    └── src/               # Source code
        ├── __init__.py    # Module initialization
        ├── auth.py        # OAuth authentication implementation
        ├── server.py      # MCP server implementation
        ├── task_monitor.py # Task monitoring system (NEW)
        └── ticktick_client.py  # TickTick API client
```

### Authentication Flow

The project implements a complete OAuth 2.0 flow for TickTick:

1. **Initial Setup**: User provides their TickTick API Client ID and Secret
2. **Browser Authorization**: User is redirected to TickTick to grant access
3. **Token Reception**: A local server receives the OAuth callback with the authorization code
4. **Token Exchange**: The code is exchanged for access and refresh tokens
5. **Token Storage**: Tokens are securely stored in the local `.env` file
6. **Token Refresh**: The client automatically refreshes the access token when it expires

This simplifies the user experience by handling the entire OAuth flow programmatically.

### Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
