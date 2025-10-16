import json # for reading and writing JSON files
from pathlib import Path # for working with file and direcotry paths 
from datetime import datetime # timestamps

def _now_iso():
    return datetime.utcnow().isoformat() + "Z" # give current time in universal coordinated time

def print_summary(changes: dict, root: Path):

    ''' 
    prints a formatted summary of detected file changes in the given directory
    grpups files into added, removed, modified, and metadata changed categories
    '''

    print(f"\n=== File Integrity Monitor @ {root} ===")

    # if all change lists are empty then print no change detected
    if all(not changes[k] for k in changes):
        print("No changes detected.")
        return

    # if any new files were added since the last baseline, list them 
    if changes["added"]:
        print("\n[ADDED]")
        for r in changes["added"]:
            print("  +", r)

    # if any files were deleted since the last baseline, list them
    if changes["removed"]:
        print("\n[REMOVED]")
        for r in changes["removed"]:
            print("  -", r)

    # if any files content changed (different hash num) then lisit then
    if changes["modified"]:
        print("\n[MODIFIED] (content changed)")
        for r in changes["modified"]:
            print("  *", r)

    # if file metadata (size or modification time) changed but content didnt then list them
    if changes["metadata_changed"]:
        print("\n[METADATA CHANGED] (mtime/size changed, content unchanged)")
        for r in changes["metadata_changed"]:
            print("  ~", r)

def save_report(changes: dict, root: Path, out: Path, append: bool = False, ndjson: bool = False):
    """
    save results either as:
      - NDJSON (newline-delimited JSON). ff ndjson=True, writes/append one JSON object per scan.
      - regular JSON:
          - if append=False: overwrite with a JSON array containing this payload.
          - if append=True: append this payload to an existing JSON array (or create one).
    """

    # ensure the output directory exists
    out.parent.mkdir(parents=True, exist_ok=True)

    # build the data payload to record scan results
    payload = {
        "root": str(root), # directory scanned
        "generated_at": _now_iso(), # timestamp
        "changes": changes, # dictionary of detected file changes
    }

    if ndjson:
        line = json.dumps(payload) # convert payload into a single JSON string
        mode = "a" if append else "w"
        with open(out, mode, encoding="utf-8") as f:
            f.write(line + "\n")
        print(f"\nSaved -> {out} ({'append' if append else 'overwrite'}, ndjson)")
        return

    # JSON file behavior 
    if append and out.exists():
        try:
            old = json.loads(out.read_text(encoding="utf-8")) # read existing JSON contnet
            if isinstance(old, list): # if it is already a list of dictionaries (multiple logs) 
                old.append(payload) # append new data
                data = old
            else:
                data = [old, payload] # is not a list, meaning there was only one log, then convert into a list containing the prev single data and the new appended data
        except Exception:
            data = [payload]
    else:
        data = [payload] # if not appending or file does not exist, start a new list with this payload

    #converts the data into a nicely formatted JSON string - easier to read
    out.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"\nSaved -> {out} ({'append' if append else 'overwrite'}, json)")
