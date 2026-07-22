"""
Verify ReplyWatcher is actively polling by monitoring for the next cycle.
This proves the async task is running, not just "started once".
"""
import time
import subprocess
import sys

print("=" * 60)
print("LIVE VERIFICATION: ReplyWatcher Active Polling")
print("=" * 60)
print()

# Get initial log size
result = subprocess.run(['wc', '-l', '../logs/backend.log'], 
                       capture_output=True, text=True)
initial_lines = int(result.stdout.split()[0])
print(f"Initial log size: {initial_lines} lines")
print()

# Wait for a bit and check for new activity
print("Monitoring for 90 seconds to catch next poll cycle...")
print("ReplyWatcher polls every 60 seconds, so we should see activity.")
print()

start_time = time.time()
max_wait = 90
check_interval = 5

last_check_lines = initial_lines

while time.time() - start_time < max_wait:
    time.sleep(check_interval)
    
    # Check current log size
    result = subprocess.run(['wc', '-l', '../logs/backend.log'], 
                           capture_output=True, text=True)
    current_lines = int(result.stdout.split()[0])
    
    elapsed = int(time.time() - start_time)
    
    # Check for new log entries
    if current_lines > last_check_lines:
        # Get new lines
        result = subprocess.run(['tail', '-n', str(current_lines - initial_lines), 
                               '../logs/backend.log'], 
                               capture_output=True, text=True)
        new_logs = result.stdout
        
        print(f"[{elapsed}s] New activity detected! ({current_lines - initial_lines} new lines)")
        
        # Check for ReplyWatcher or orchestrator activity
        if 'ReplyWatcher' in new_logs:
            print("✅ ReplyWatcher activity found:")
            for line in new_logs.split('\n'):
                if 'ReplyWatcher' in line:
                    print(f"   {line}")
        
        if 'orchestrator' in new_logs.lower() or 'queue' in new_logs.lower():
            print("✅ Orchestrator/Queue activity found:")
            for line in new_logs.split('\n'):
                if 'orchestrator' in line.lower() or 'queue' in line.lower():
                    print(f"   {line}")
        
        last_check_lines = current_lines
    else:
        sys.stdout.write(f"\r[{elapsed}s] Waiting... (log size: {current_lines} lines)")
        sys.stdout.flush()

print()
print()
print("=" * 60)
print("Verification Complete")
print("=" * 60)

# Final check
result = subprocess.run(['tail', '-20', '../logs/backend.log'], 
                       capture_output=True, text=True)
print("\nLast 20 log lines:")
print(result.stdout)

