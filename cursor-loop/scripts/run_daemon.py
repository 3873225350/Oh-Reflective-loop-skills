import subprocess
import time
import os
import sys
import re
from datetime import datetime

# --- Configuration (Relative to Workspace) ---
STATE_DIR = ".cursor-loop/state"
# LOG_DIR and ACTIVE_LOG_LINK are set per-loop in setup_environment()
ROADMAP_FILE = "ROADMAP.md"
DISPATCH_SCRIPT_NAME = "dispatch_agent.sh"
INTERVAL = 60

def get_metadata():
    plan_id = "UNKNOWN-PLAN"
    task_id = "INIT"
    total_tasks = 0
    try:
        # Check current loop state dir first if possible, otherwise root
        # This run_daemon is called with LOOP_NAME
        loop_name = os.environ.get("LOOP_NAME", "OPTIMIZE_ROADMAP")
        loop_roadmap = os.path.join(STATE_DIR, loop_name, f"{loop_name}.md")
        target_file = loop_roadmap if os.path.exists(loop_roadmap) else ROADMAP_FILE

        if os.path.exists(target_file):
            with open(target_file, "r") as f:
                content = f.read()
                plan_match = re.search(r"Plan ID\*\*: `([^`]+)`", content)
                if plan_match: plan_id = plan_match.group(1)

                task_match = re.search(r"Active Task\*\*: `([^`]+)`", content)
                if task_match: task_id = task_match.group(1)

                # Count all tasks in roadmap: - [ ] **...** or - [x] **...**
                all_tasks = re.findall(r"- \[[ xX]\] \*\*([^*]+)\*\*", content)
                total_tasks = len(all_tasks)
    except:
        pass
    return plan_id, task_id, total_tasks

def log_to_file(file_path, msg):
    with open(file_path, "a") as f:
        f.write(msg)
        f.flush()
        os.fsync(f.fileno())

def setup_environment():
    loop_name = os.environ.get("LOOP_NAME", "default")
    loop_state_dir = os.path.join(STATE_DIR, loop_name)
    LOG_DIR = os.path.join(loop_state_dir, "logs")
    ACTIVE_LOG_LINK = os.path.join(loop_state_dir, "active.log")
    PID_FILE = os.path.join(loop_state_dir, "daemon.pid")

    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

    plan_id, _, _ = get_metadata()
    pid = os.getpid()
    start_time = datetime.now().strftime("%Y%m%d-%H%M%S")
    instance_log = os.path.join(LOG_DIR, f"loop-{plan_id}-PID{pid}-{start_time}.log")

    # Write PID file for health checks
    with open(PID_FILE, "w") as f:
        f.write(str(pid))

    if os.path.exists(ACTIVE_LOG_LINK):
        if os.path.islink(ACTIVE_LOG_LINK) or os.path.isfile(ACTIVE_LOG_LINK):
            os.remove(ACTIVE_LOG_LINK)

    try:
        os.symlink(instance_log, ACTIVE_LOG_LINK)
    except:
        with open(ACTIVE_LOG_LINK, "w") as f: f.write(instance_log)

    return plan_id, pid, instance_log

def log(msg, plan_id, pid, instance_log, indent=0, sub_pid="-----"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    _, curr_task, total = get_metadata()
    prefix = "  " * indent
    # Professional Supervised Format: [TIMESTAMP] [Supervised-PID:PID|||PLAN] [Sub-PID: SUBPID|||TASK/TOTAL]
    header = f"[Supervised-PID:{pid}|||{plan_id}] [Sub-PID: {sub_pid}|||{curr_task}/{total}]"
    formatted = f"[{timestamp}] {header} {prefix}{msg}\n"
    print(formatted, end="")
    log_to_file(instance_log, formatted)

def run():
    plan_id, pid, instance_log = setup_environment()
    script_dir = os.path.dirname(os.path.realpath(__file__))
    dispatch_script = os.path.join(script_dir, DISPATCH_SCRIPT_NAME)
    loop_name = os.environ.get("LOOP_NAME", "OPTIMIZE_ROADMAP")

    log("╔════════════════════════════════════════════════════════════════", plan_id, pid, instance_log)
    log("║ SESSION START: Cursor Loop Orchestrator (Supervised + Reflective)", plan_id, pid, instance_log)
    log(f"║ Plan ID: {plan_id}", plan_id, pid, instance_log)
    log(f"║ Log File: {instance_log}", plan_id, pid, instance_log)
    log("╚════════════════════════════════════════════════════════════════", plan_id, pid, instance_log)

    while True:
        log("▶▶▶ NEXT TICK START ◀◀◀", plan_id, pid, instance_log)

        last_mode = "check"
        loop_state_file = os.path.join(STATE_DIR, loop_name, "last_mode.txt")
        if os.path.exists(loop_state_file):
            try:
                with open(loop_state_file, "r") as f: last_mode = f.read().strip()
            except: pass

        next_mode = "optimize" if last_mode == "check" else "check"
        log(f"TARGET MODE: {next_mode}", plan_id, pid, instance_log, indent=1)

        try:
            process = subprocess.Popen(
                [dispatch_script, next_mode, loop_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                cwd=os.environ.get("WORKSPACE", ".")
            )
            
            log(f"Expert Dispatcher Active", plan_id, pid, instance_log, indent=1, sub_pid=process.pid)
            
            for line in process.stdout:
                log(f"[Agent] {line.strip()}", plan_id, pid, instance_log, indent=2, sub_pid=process.pid)
                
            process.wait()
            
            if process.returncode == 0:
                log(f"SUCCESS: {next_mode} completed.", plan_id, pid, instance_log, indent=1)
                with open(loop_state_file, "w") as f:
                    f.write(next_mode)
            else:
                log(f"WARNING: Dispatch finished with code {process.returncode}", plan_id, pid, instance_log, indent=1)
                
        except Exception as e:
            log(f"CRITICAL FAILURE: {str(e)}", plan_id, pid, instance_log, indent=1)

        log("■■■ TICK FINISHED ■■■", plan_id, pid, instance_log)
        log(f"Resting for {INTERVAL}s...", plan_id, pid, instance_log, indent=1)
        time.sleep(INTERVAL)

if __name__ == "__main__":
    run()
