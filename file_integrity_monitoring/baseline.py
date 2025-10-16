import json # for reading/writing JSON files
import time # for timestamps and sleep intervals
from pathlib import Path # for handling file paths
from dataclasses import dataclass # for creating simple classes to hold data
from typing import Dict # for type hinting
from file_integrity_monitoring.hasher import sha256_file # to compute file hashes
from file_integrity_monitoring.ignore import is_ignored # to check if a file should be ignored based on patterns

@dataclass 
class FileInfo:
    sha256: str
    size: int
    mtime: float

def _rel(p: Path, root: Path):
    '''
    convert a full file path into a shorter relative to the given root folder
    makes the stored file names easier to read and consistent in the snapshot
     - example: "C:/Users/Kate/watchme/notes.txt" → "notes.txt"
    '''
    return str(p.relative_to(root).as_posix())

def walk_and_hash(root: Path, ignore_patterns):
    """
    walks through the whole folder/files that isnt ignored
    for each file, computes its sha256 hash, size, and modification time
    returns a dictionary (snapshot) that maps each file's path to that info
    """

    snapshot: Dict[str, dict] = {} # empty dictionary to hold file info

    # for each file in the root directory and its subdirectories
    for p in root.rglob("*"): # look at everything under this folder

        # if it is not a file, skip it
        # if it is a folder that has a file in it we will keep going down until we find a file
        if not p.is_file(): 
            continue

        # converts the path to a short relative path
        # example: if root is /home/user/docs and p is /home/user/docs/file.txt, rel will be file.txt
        rel = _rel(p, root) 

        # if the file matches any ignore patterns, skip it
        if is_ignored(root, rel, ignore_patterns):
            continue

        # try to get the file's stats (size, mtime) and compute its sha256 hash
        try:
            stat = p.stat() # get file stats - size, modification time, creation/acess time, etc

            # reads the file and computes its sha256 hash
            info = FileInfo( 
                sha256=sha256_file(p), # compute sha256 hash of the file
                size=stat.st_size, # get file size in bytes
                mtime=stat.st_mtime # get last modification time 
            )

            # store the file's info in the snapshot dictionary using its relative path as the key
            snapshot[rel] = info.__dict__ 
        except (PermissionError, FileNotFoundError):
            # skip unreadable/vanished files
            continue
    return snapshot

def save_baseline(snapshot: dict, path: Path):
    '''
    saves the current folder snapshot to a JSON file, aka the baseline
    this file acts as the "safe state" record for future comparisions
    '''

    # make a dictionary that stores the current time, schema version, and all file data
    payload = {"created_utc": time.time(), "schema": 1, "files": snapshot}

    # convert the dictionary to a JSON string and write it to the given file path given
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

def load_baseline(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "files" not in data:
        raise ValueError("Invalid baseline file")
    return data["files"]

def compare_snapshots(old: dict, new: dict):
    """
    return changes between two snapshots:
      {
        added: [rel],             # new files in new that didnt exist before
        removed: [rel],           # files that existed in old but are now gone
        modified: [rel],          # hash changed (contents of file changed)
        metadata_changed: [rel],  # size/mtime changed but hash same
      }
    """

    old_keys = set(old.keys()) # all file paths in the old baseline
    new_keys = set(new.keys()) #all file paths in the new scan

    added = sorted(new_keys - old_keys) # files that only appear in new snapchat
    removed = sorted(old_keys - new_keys) # files that were in the old snapshot but no longer exist (deleted)

    modified = [] 
    meta_changed = []

    # for files (relative path) that exist in both snapshots we check for modification or metadata changes
    for rel in sorted(old_keys & new_keys):
        o, n = old[rel], new[rel] 
        if o["sha256"] != n["sha256"]: # if hash no longer are equal
            modified.append(rel) # add to modified list
        else: # if size no longer are equal
            if o.get("size") != n.get("size") or int(o.get("mtime", 0)) != int(n.get("mtime", 0)):
                meta_changed.append(rel) # add to meta_changed list

    return {
        "added": added,
        "removed": removed,
        "modified": modified,
        "metadata_changed": meta_changed,
    }
