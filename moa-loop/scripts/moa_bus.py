#!/usr/bin/env python3
#================================================================
# MOA Bus - FIFO + SQLite Hybrid Communication System
# High-speed message passing + persistent storage
#================================================================

import os
import sys
import json
import time
import sqlite3
import threading
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any

class MOABus:
    """
    FIFO + SQLite Hybrid Communication System

    FIFO: Real-time message passing (microseconds)
    SQLite: Persistent storage and queries
    """

    def __init__(self, bus_name: str = "default", base_dir: str = "/tmp/moa_bus"):
        self.bus_name = bus_name
        self.base_dir = Path(base_dir) / bus_name
        self.base_dir.mkdir(parents=True, exist_ok=True)

        # FIFO paths
        self.fifo_dir = self.base_dir / "fifos"
        self.fifo_dir.mkdir(exist_ok=True)

        # SQLite database
        self.db_path = self.base_dir / "context.db"

        # Initialize
        self._init_fifo_dir()
        self._init_database()

        # Lock for thread safety
        self._lock = threading.Lock()

        # Active listeners
        self._listeners: Dict[str, threading.Thread] = {}
        self._running = True

    def _init_fifo_dir(self):
        """Create FIFO pipes for each agent"""
        self.fifos: Dict[str, str] = {}

        agents = ["coordinator", "gemini", "claude", "qwen", "kimi", "cursor", "minimax"]
        for agent in agents:
            fifo_path = self.fifo_dir / f"{agent}.fifo"
            self.fifos[agent] = str(fifo_path)

            if not fifo_path.exists():
                os.mkfifo(fifo_path)
                print(f"Created FIFO: {fifo_path}")

    def _init_database(self):
        """Initialize SQLite database with schema"""
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

        cursor = self.conn.cursor()

        # Messages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender TEXT NOT NULL,
                recipient TEXT,
                msg_type TEXT NOT NULL,
                content TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                read INTEGER DEFAULT 0
            )
        """)

        # Agents table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agents (
                name TEXT PRIMARY KEY,
                capabilities TEXT,
                status TEXT DEFAULT 'offline',
                registered_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_seen TEXT
            )
        """)

        # Knowledge table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS knowledge (
                key TEXT PRIMARY KEY,
                value TEXT,
                added_by TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Tasks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                task_id TEXT PRIMARY KEY,
                description TEXT,
                assigned_to TEXT,
                status TEXT DEFAULT 'pending',
                result TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                completed_at TEXT
            )
        """)

        # State table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS state (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        self.conn.commit()
        print(f"Initialized database: {self.db_path}")

    # ==================== FIFO Operations ====================

    def send_fifo(self, recipient: str, message: Dict[str, Any]) -> bool:
        """Send message via FIFO (non-blocking)"""
        try:
            fifo_path = self.fifos.get(recipient)
            if not fifo_path:
                return False

            with open(fifo_path, 'w') as f:
                json.dump(message, f)
                f.write('\n')
                f.flush()
            return True
        except Exception as e:
            print(f"FIFO send error: {e}")
            return False

    def recv_fifo(self, agent: str, timeout: float = 0.1) -> Optional[Dict]:
        """Receive message from FIFO (with timeout)"""
        fifo_path = self.fifos.get(agent)
        if not fifo_path:
            return None

        try:
            # Use select-like polling
            fd = os.open(fifo_path, os.O_RDONLY | os.O_NONBLOCK)
            import select

            readable, _, _ = select.select([fd], [], [], timeout)

            if readable:
                data = os.read(fd, 4096).decode()
                os.close(fd)
                return json.loads(data.strip())

            os.close(fd)
            return None
        except Exception as e:
            return None

    def post_message(self, sender: str, recipient: str, msg_type: str, content: str):
        """Post message (FIFO + SQLite)"""
        message = {
            "sender": sender,
            "recipient": recipient,
            "type": msg_type,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }

        # Send via FIFO
        if recipient != "broadcast":
            self.send_fifo(recipient, message)

        # Store in SQLite
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO messages (sender, recipient, msg_type, content)
                VALUES (?, ?, ?, ?)
            """, (sender, recipient, msg_type, content))
            self.conn.commit()

        return message

    def broadcast(self, sender: str, msg_type: str, content: str):
        """Broadcast message to all agents"""
        for agent in self.fifos.keys():
            if agent != sender:
                self.post_message(sender, agent, msg_type, content)

    # ==================== SQLite Operations ====================

    def register_agent(self, name: str, capabilities: List[str]):
        """Register an agent"""
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO agents (name, capabilities, status, last_seen)
                VALUES (?, ?, 'active', CURRENT_TIMESTAMP)
            """, (name, ",".join(capabilities)))
            self.conn.commit()

    def update_agent_heartbeat(self, name: str):
        """Update agent last seen time"""
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute("""
                UPDATE agents SET last_seen = CURRENT_TIMESTAMP WHERE name = ?
            """, (name,))
            self.conn.commit()

    def get_active_agents(self) -> List[Dict]:
        """Get all active agents (seen in last 60s)"""
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT * FROM agents
                WHERE status = 'active'
                AND datetime(last_seen) > datetime('now', '-60 seconds')
            """)
            return [dict(row) for row in cursor.fetchall()]

    def add_knowledge(self, key: str, value: str, added_by: str):
        """Add to shared knowledge base"""
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO knowledge (key, value, added_by)
                VALUES (?, ?, ?)
            """, (key, value, added_by))
            self.conn.commit()

    def query_knowledge(self, key: str) -> Optional[str]:
        """Query knowledge by key"""
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute("SELECT value FROM knowledge WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row['value'] if row else None

    def list_knowledge(self) -> List[Dict]:
        """List all knowledge"""
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM knowledge ORDER BY timestamp DESC")
            return [dict(row) for row in cursor.fetchall()]

    def create_task(self, task_id: str, description: str, assigned_to: str):
        """Create a new task"""
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO tasks (task_id, description, assigned_to)
                VALUES (?, ?, ?)
            """, (task_id, description, assigned_to))
            self.conn.commit()

    def update_task(self, task_id: str, status: str, result: str = None):
        """Update task status and result"""
        with self._lock:
            cursor = self.conn.cursor()
            if result:
                cursor.execute("""
                    UPDATE tasks SET status = ?, result = ?,
                    completed_at = CURRENT_TIMESTAMP WHERE task_id = ?
                """, (status, result, task_id))
            else:
                cursor.execute("""
                    UPDATE tasks SET status = ? WHERE task_id = ?
                """, (status, task_id))
            self.conn.commit()

    def get_task(self, task_id: str) -> Optional[Dict]:
        """Get task by ID"""
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def list_tasks(self, status: str = None) -> List[Dict]:
        """List tasks, optionally filtered by status"""
        with self._lock:
            cursor = self.conn.cursor()
            if status:
                cursor.execute("SELECT * FROM tasks WHERE status = ?", (status,))
            else:
                cursor.execute("SELECT * FROM tasks")
            return [dict(row) for row in cursor.fetchall()]

    def set_state(self, key: str, value: str):
        """Set global state"""
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO state (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (key, value))
            self.conn.commit()

    def get_state(self, key: str) -> Optional[str]:
        """Get global state"""
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute("SELECT value FROM state WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row['value'] if row else None

    # ==================== Query Interface ====================

    def query(self, sql: str) -> List[Dict]:
        """Execute custom SQL query"""
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute(sql)
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def show_summary(self):
        """Display bus summary"""
        print("\n" + "="*60)
        print(f"MOA Bus: {self.bus_name}")
        print("="*60)

        print("\n📊 Agents:")
        for agent in self.get_active_agents():
            caps = agent.get('capabilities', '').split(',')
            print(f"  ✅ {agent['name']}: {caps}")

        print("\n📚 Knowledge:")
        for item in self.list_knowledge()[:5]:
            print(f"  {item['key']}: {item['value'][:50]}...")

        print("\n📋 Tasks:")
        pending = [t for t in self.list_tasks() if t['status'] == 'pending']
        completed = [t for t in self.list_tasks() if t['status'] == 'completed']
        print(f"  Pending: {len(pending)}")
        print(f"  Completed: {len(completed)}")

        print("\n" + "="*60)

    def close(self):
        """Close bus"""
        self._running = False
        self.conn.close()


# CLI Interface
def main():
    if len(sys.argv) < 2:
        print("Usage: moa_bus.py <command> [args...]")
        print("\nCommands:")
        print("  init                          - Initialize bus")
        print("  post <to> <type> <content>   - Post message")
        print("  broadcast <type> <content>   - Broadcast message")
        print("  agents                        - List active agents")
        print("  knowledge add <key> <value>  - Add knowledge")
        print("  knowledge list                - List knowledge")
        print("  task create <id> <desc> <to> - Create task")
        print("  task list [status]           - List tasks")
        print("  state set <key> <value>     - Set state")
        print("  state get <key>              - Get state")
        print("  query <sql>                  - Custom SQL query")
        print("  summary                      - Show summary")
        sys.exit(1)

    bus = MOABus()
    cmd = sys.argv[1]

    try:
        if cmd == "init":
            print("Bus initialized")
            bus.show_summary()

        elif cmd == "post":
            _, to, msg_type, content = sys.argv
            bus.post_message("cli", to, msg_type, content)
            print(f"Posted to {to}")

        elif cmd == "broadcast":
            _, msg_type, content = sys.argv
            bus.broadcast("cli", msg_type, content)
            print("Broadcast sent")

        elif cmd == "register":
            name = sys.argv[2]
            caps = sys.argv[3:] if len(sys.argv) > 3 else []
            bus.register_agent(name, caps)
            print(f"Registered: {name} ({','.join(caps)})")

        elif cmd == "agents":
            for agent in bus.get_active_agents():
                print(f"{agent['name']}: {agent['capabilities']}")

        elif cmd == "knowledge":
            if len(sys.argv) >= 4 and sys.argv[2] == "add":
                key = sys.argv[3]
                value = " ".join(sys.argv[4:])
                bus.add_knowledge(key, value, "cli")
                print(f"Added: {key}")
            elif sys.argv[2] == "list":
                for item in bus.list_knowledge():
                    print(f"{item['key']}: {item['value']}")

        elif cmd == "task":
            if len(sys.argv) >= 5 and sys.argv[2] == "create":
                task_id = sys.argv[3]
                assigned = sys.argv[4]
                desc = " ".join(sys.argv[5:])
                bus.create_task(task_id, desc, assigned)
                print(f"Created task: {task_id}")
            elif sys.argv[2] == "list":
                status = sys.argv[3] if len(sys.argv) > 3 else None
                for task in bus.list_tasks(status):
                    print(f"{task['task_id']}: {task['status']} -> {task['assigned_to']}")

        elif cmd == "state":
            if sys.argv[2] == "set":
                _, _, key, value = sys.argv
                bus.set_state(key, value)
                print(f"Set: {key}")
            elif sys.argv[2] == "get":
                _, _, key = sys.argv
                print(bus.get_state(key))

        elif cmd == "query":
            _, sql = sys.argv
            for row in bus.query(sql):
                print(row)

        elif cmd == "summary":
            bus.show_summary()

    finally:
        bus.close()


if __name__ == "__main__":
    main()
