# File Integrity Monitoring (FIM)
  A Python-based **File Integrity Monitoring (FIM)** tool that detects file additions, deletions, and modifications
  using **SHA-256 hashing**. Supports baseline creation, real-time monitoring, and ignore patterns.

# Features
 - **SHA-256 hashing** - Detects any file content change
 - **Baseline management** – Save a snapshot of the known good state
 - **Change detection** – Identify added, removed, or modified files
 - **Ignore patterns** – Skip logs, temp files, or any unwanted files
 -  **Real-time monitoring** – Continuous scanning at custom intervals
 -  **JSON / NDJSON reports** – Easy to log or automate results
 -   **UTC timestamps** – Universal time tracking in ISO format

# Setup 
## 1. Initialize a baseline
 - No external libraries — the entire project uses Python’s standard library
 - ```bash
    git clone https://github.com/kateserem/file-integrity-monitoring.git
    cd file-integrity-monitoring

## 2. Run a Scan
    python -m file_integrity_monitoring.main "watchme" scan
   
## 3. Detect Ignored Files
    *.log
    temp*
    then scan with: python -m file_integrity_monitoring.main "watchme" scan --ignore "watchme/ignore.csv"
  
## 4. Continuous Monitoring
    python -m file_integrity_monitoring.main "watchme" monitor --interval 5 -o fim_log.ndjson --ndjson --append

## 5. Accept Current State
    python -m file_integrity_monitoring.main "watchme" accept

# Example Output 

## Sample Pretty JSON Log - Easier to Read
    {
      "root": "watchme",
      "generated_at": "2025-10-16T18:32:47Z",
      "changes": {
        "added": ["example.txt"],
        "removed": ["old_file.txt"],
        "modified": ["notes.docx"],
        "metadata_changed": []
      }
    }
## Sample NDJSON Line
    {"root": "watchme", "generated_at": "2025-10-16T18:32:47Z", "changes": {"added": ["example.txt"], "removed": ["old_file.txt"], "modified": ["notes.docx"], "metadata_changed": []}}

# Folder Structure
    file-integrity-monitoring/
    │
    ├── file_integrity_monitoring/
    │   ├── baseline.py
    │   ├── hasher.py
    │   ├── ignore.py
    │   ├── reporter.py
    │   └── main.py
    │
    ├── watchme/
    │   ├── file1.txt
    │   └── ignore.csv
    │
    ├── sample_fim_log_pretty.json
    └── README.md

  # How it Works
          | Function              | Description                             |
    | --------------------- | --------------------------------------------- |
    | `walk_and_hash()`     | walks through files, computing SHA-256 hashes |
    | `save_baseline()`     | saves baseline snapshot to JSON               |
    | `load_baseline()`     | loads an existing baseline for comparison     |
    | `compare_snapshots()` | finds added, removed, or modified files       |
    | `print_summary()`     | prints readable scan summary                  |
    | `save_report()`       | exports JSON/NDJSON results                   |
    | `_now_iso()`          | returns UTC timestamp in ISO format           |

# Example Workflow
  # 1. Create baseline
    python -m file_integrity_monitoring.main "watchme" init
  
  # 2. Edit or delete a file
    echo "new line" >> watchme/file1.txt
  
  # 3. Scan for changes
    python -m file_integrity_monitoring.main "watchme" scan
  
  # 4. Ignore temp files
    python -m file_integrity_monitoring.main "watchme" init --ignore "watchme/ignore.csv"
  
  # 5. Continuous monitor
    python -m file_integrity_monitoring.main "watchme" monitor --interval 5

# Author
  Kate Serem
  
  Computer Engineering and Cybersecurity
  
  Texas A&M University
