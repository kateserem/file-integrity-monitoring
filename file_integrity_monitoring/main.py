import argparse # for parse command-line arguments
import time # for timestamps
from pathlib import Path # for handling file and directory paths in os
from typing import Optional # can be the data type request or None

# import core functions for scanning and comparing file states
from file_integrity_monitoring.baseline import (
    walk_and_hash,
    save_baseline,
    load_baseline,
    compare_snapshots,
)
# import helper for ignore file patters
from file_integrity_monitoring.ignore import load_ignore_patterns

#import reporting utilities to display and save scan result
from file_integrity_monitoring.reporter import print_summary, save_report

DEFAULT_BASELINE = ".fim_baseline.json"

def parse_args():
    p = argparse.ArgumentParser(
        prog="fim",
        description="File Integrity Monitor: baseline a folder and detect changes",
    )
    p.add_argument("root", type=Path, help="Root directory to monitor")

    sub = p.add_subparsers(dest="cmd", required=True)

    # init
    s_init = sub.add_parser("init", help="Create a baseline snapshot for ROOT")
    s_init.add_argument("--ignore", type=str, default=None,
                        help='Comma-separated ignore globs (e.g., "*.log,*.tmp")')
    s_init.add_argument("--baseline", type=Path, default=None,
                        help=f"Baseline file path (default: ROOT/{DEFAULT_BASELINE})")

    # scan (supports multi-run, append, ndjson, accept-baseline)
    s_scan = sub.add_parser("scan", help="Compare current state to baseline and emit report")
    s_scan.add_argument("--ignore", type=str, default=None)
    s_scan.add_argument("--baseline", type=Path, default=None)
    s_scan.add_argument("-o", "--out", type=Path, default=Path("fim_report.json"),
                        help="Write report here (json or ndjson)")
    s_scan.add_argument("--append", action="store_true",
                        help="Append results instead of overwriting")
    s_scan.add_argument("--ndjson", action="store_true",
                        help="Emit newline-delimited JSON (one JSON object per line)")
    s_scan.add_argument("--interval", type=int, default=0,
                        help="Repeat scan every N seconds (0 = run once)")
    s_scan.add_argument("--max-runs", type=int, default=1,
                        help="Number of scans to run (default 1)")
    s_scan.add_argument("--accept-baseline", action="store_true",
                        help="After finishing the scan(s), update the baseline to the current state")

    # accept (promote current state to baseline without scanning)
    s_acc = sub.add_parser("accept", help="Promote current on-disk state to the baseline")
    s_acc.add_argument("--ignore", type=str, default=None)
    s_acc.add_argument("--baseline", type=Path, default=None)

    # monitor (poll forever)
    s_mon = sub.add_parser("monitor", help="Continuously scan & report changes")
    s_mon.add_argument("--ignore", type=str, default=None)
    s_mon.add_argument("--baseline", type=Path, default=None)
    s_mon.add_argument("--interval", type=int, default=15, help="Seconds between scans (default 15)")
    s_mon.add_argument("-o", "--out", type=Path, default=Path("fim_report.json"))
    s_mon.add_argument("--append", action="store_true",
                       help="Append results each interval")
    s_mon.add_argument("--ndjson", action="store_true",
                       help="Use newline-delimited JSON for continuous logging")

    return p.parse_args()

def baseline_path(root: Path, override: Optional[Path]):
    '''determine where the baseline file is or will be located'''

    # if override is given, use that. otherwise use default location (root/.fim_baseline.json)
    return (override if override else (root / DEFAULT_BASELINE))

def _ensure_root_exists(root: Path):
    '''checks if the folder we want to monitor exists'''

    #if the root directory does not exist, exit the program with an error message
    if not root.exists():
        raise SystemExit(f"[error] root folder does not exist: {root}")

def do_init(root: Path, ignore_csv: Optional[str], baseline_file: Optional[Path]):
    '''
    takes a picture of what this folder looks like right now and saves it as a baseline
    creating the baseline
    "clean slate" snapshot of directory for the very first time
    '''

    root = root.resolve() # absolute full path for root
    _ensure_root_exists(root) # check if root exists
    bl = baseline_path(root, baseline_file) # find where to save the baseline file; uses default (watchme/.fim_baseline.json) if none is given. know where to write data
    patterns = load_ignore_patterns(root, ignore_csv) # skip unnecessary files by reading .fimignore or --ignore
    snap = walk_and_hash(root, patterns) # take a snapshot of the current state of the folder
    save_baseline(snap, bl) # write the snapshot to the baseline file for future comparisons
    print(f"Baseline created -> {bl}  (files tracked: {len(snap)})") # inform user of success

def do_scan(root: Path, ignore_csv: Optional[str], baseline_file: Optional[Path],
            out: Path, append: bool, ndjson: bool, interval: int, max_runs: int,
            accept_baseline: bool):
    """
    - using an existing baseline to detect changes

    perform one or multiple scans
     - If interval > 0 and max_runs>1, repeat N times.
    uses a rolling in-memory comparison so later runs only show new changes.
    optionally updates the baseline at the end (--accept-baseline).

    fim scan --interval N --max-runs M
    """

    root = root.resolve() 
    _ensure_root_exists(root) 
    bl = baseline_path(root, baseline_file)

    # if the baseline file does not exist, stop execution
        # if baseline file was deleted, renamed, or moved manually while running --interval scans
    if not bl.exists():
        raise SystemExit(f"[error] baseline not found: {bl}. Run 'fim {root} init' first.")
    
    patterns = load_ignore_patterns(root, ignore_csv)
    old = load_baseline(bl)  # load the previous baseline snapshot

    # loop through each scan run
    for run in range(1, max_runs + 1):
        new = walk_and_hash(root, patterns) # scan the directory and compute file hashes
        changes = compare_snapshots(old, new) # compare old and new snapshot to detect changes
        print(f"\nRun {run}/{max_runs}:")
        print_summary(changes, root)
        save_report(changes, root, out, append=append, ndjson=ndjson)
        old = new  # update new baseline 
        if interval > 0 and run < max_runs:
            time.sleep(interval)

    # if --accept-baseline enabled, make the latest snapshot as the new "safe"
    if accept_baseline:
        save_baseline(old, bl)  # old is the latest snapshot after the loop
        print(f"\nBaseline updated -> {bl}")

def do_accept(root: Path, ignore_csv: Optional[str], baseline_file: Optional[Path]):
    """
    updates (or creates) the baseline immediately, without running a scan or printing change logs

    "whatever the current folder looks like right now, treat that as the new trusted baseline"
    """

    root = root.resolve()
    _ensure_root_exists(root)
    bl = baseline_path(root, baseline_file)
    patterns = load_ignore_patterns(root, ignore_csv)
    snap = walk_and_hash(root, patterns) # scan the directory and compute file hashes
    save_baseline(snap, bl)
    print(f"Baseline updated -> {bl}  (files tracked: {len(snap)})")

def do_monitor(root: Path, ignore_csv: Optional[str], baseline_file: Optional[Path],
               out: Path, interval: int, append: bool, ndjson: bool):
    '''
    continuous monitoring move, forever until ctrl + C

    fim monitor --interval N
    '''
    root = root.resolve()
    _ensure_root_exists(root)
    bl = baseline_path(root, baseline_file)

    if not bl.exists():
        raise SystemExit(f"[error] baseline not found: {bl}. Run 'fim {root} init' first.")
    patterns = load_ignore_patterns(root, ignore_csv)
    old = load_baseline(bl)

    print(f"Monitoring {root} every {interval}s. Press Ctrl+C to stop.")
    while True:
        try:
            new = walk_and_hash(root, patterns)
            changes = compare_snapshots(old, new)
            print_summary(changes, root)
            save_report(changes, root, out, append=append, ndjson=ndjson)
            old = new
            time.sleep(interval)
        except KeyboardInterrupt:
            print("\nStopping monitor.")
            break

def main():
    args = parse_args()

    if args.cmd == "init": # save current folder/file as baseline aka "safe". well check if changed later
        do_init(args.root, args.ignore, args.baseline) 

    elif args.cmd == "scan": # compare current state to baseline and emit report
        do_scan(
            args.root, # root directory to monitor
            args.ignore, # optional ignore patterns
            args.baseline, # optional baseline file path
            args.out, # output report file path
            args.append, # append to report file instead of overwriting
            args.ndjson, # use JSON format
            args.interval, # seconds between scans (0 = run once)
            args.max_runs, # number of scans to run
            args.accept_baseline # update baseline to current state after scans
        )
    elif args.cmd == "accept": # if we trust current state, then promote it to base line without scanning
        do_accept(args.root, args.ignore, args.baseline
        )
    elif args.cmd == "monitor": # continuously scan & report changes
        do_monitor(args.root, args.ignore, args.baseline, args.out, args.interval, args.append, args.ndjson)

if __name__ == "__main__":
    main()
