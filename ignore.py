from pathlib import Path # for working with file and direcotry paths 
from fnmatch import fnmatch # for matching filenames against patterns (*.tmp, *.log)
from typing import List, Optional #

def load_ignore_patterns(root: Path, ignore_from: Optional[str]) -> List[str]:
    """
    load ignore patterns from:
      1) a .fimignore file at root
      2) an optional --ignore CLI string
    always ignores the baseline file itself.
    """
    patterns: List[str] = []

    # .fimignore in root
        # .fimignore tells the program which files/folders to ignore when taking a snapshot of the folder

    #if there is a .fimignore file in the root directory, read it and add its patterns to the ignore list
    f = root / ".fimignore"
    if f.exists(): # if the .fimignore file exists
        try:
            # read each line of the .fimignore file
            for line in f.read_text(encoding="utf-8", errors="ignore").splitlines():
                line = line.strip() # remove leading/trailing whitespace
                if not line or line.startswith("#"): # skip empty lines and comments
                    continue 
                patterns.append(line) # add the pattern to the list
        except Exception:
            pass

    # --ignore CLI (comma separated)
    # if the user provided additional ignore patterns via the command line, add those too
    if ignore_from:
        for part in ignore_from.split(","): # split the string by commas
            pat = part.strip() 
            if pat: # if the pattern is not empty
                patterns.append(pat)

    # always ignore our baseline JSON if it lives under root
    patterns.append(".fim_baseline.json")
    return patterns

def is_ignored(root: Path, relpath: str, patterns: List[str]) -> bool:
    """
    checks if a file should be skipped based on ignore patterns (like from .fimignore)
    if the files name or path matchhes a pattern, it returns True
        otherwise it returns false
    """
    name = Path(relpath).name  # get the filename

    # go through every ignored pattern
    for pat in patterns: 
        if fnmatch(name, pat) or fnmatch(relpath, pat): # if match found, ignore the file
            return True
    return False
