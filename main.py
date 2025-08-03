"""Demo script showing how to use the log analyzer."""

from src.oplog_analysis.log_analyzer import analyze_log
import os

def main():
    """Demo analyzing a log file if available."""
    logs_dir = "logs"
    if os.path.exists(logs_dir):
        log_files = [f for f in os.listdir(logs_dir) if f.endswith('.log')]
        if log_files:
            log_file = os.path.join(logs_dir, log_files[0])
            print(f"Analyzing sample log: {log_file}")
            analyze_log(log_file)
        else:
            print("No log files found in logs/ directory")
    else:
        print("No logs directory found. Place JuiceFS log files in logs/ directory.")

if __name__ == "__main__":
    main()
