#!/usr/bin/env python3
"""dupefind - Find duplicate files by content hash. Zero deps."""
import sys, os, hashlib, json
from collections import defaultdict

def hash_file(path, quick=False):
    h = hashlib.md5()
    try:
        with open(path, "rb") as f:
            if quick:
                h.update(f.read(4096))  # First 4KB only
            else:
                while chunk := f.read(8192):
                    h.update(chunk)
        return h.hexdigest()
    except: return None

def scan(root, min_size=1, max_size=None, exts=None):
    files_by_size = defaultdict(list)
    
    skip = {".git","node_modules","__pycache__",".venv","venv",".Trash"}
    
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in skip]
        for f in filenames:
            if f.startswith("."): continue
            path = os.path.join(dirpath, f)
            if not os.path.isfile(path): continue
            
            if exts:
                ext = os.path.splitext(f)[1].lower()
                if ext not in exts: continue
            
            try:
                size = os.path.getsize(path)
            except: continue
            
            if size < min_size: continue
            if max_size and size > max_size: continue
            
            files_by_size[size].append(path)
    
    # Only check sizes with multiple files
    candidates = {s: paths for s, paths in files_by_size.items() if len(paths) > 1}
    
    # Hash candidates
    dupes = defaultdict(list)
    for size, paths in candidates.items():
        # Quick hash first
        quick_groups = defaultdict(list)
        for p in paths:
            qh = hash_file(p, quick=True)
            if qh: quick_groups[qh].append(p)
        
        # Full hash only quick-hash matches
        for qh, qpaths in quick_groups.items():
            if len(qpaths) < 2: continue
            for p in qpaths:
                fh = hash_file(p)
                if fh: dupes[fh].append((p, size))
    
    return {h: group for h, group in dupes.items() if len(group) > 1}

def fmt_size(b):
    if b >= 1048576: return f"{b/1048576:.1f}MB"
    if b >= 1024: return f"{b/1024:.1f}KB"
    return f"{b}B"

def cmd_find(args):
    root = "."
    min_size = 1
    exts = None
    
    for i, a in enumerate(args):
        if a == "--min" and i+1 < len(args): min_size = int(args[i+1])
        elif a == "--ext" and i+1 < len(args): exts = set(args[i+1].split(","))
        elif not a.startswith("-"): root = a
    
    root = os.path.abspath(root)
    print(f"🔍 Scanning {root}...\n")
    
    dupes = scan(root, min_size=min_size, exts=exts)
    
    if not dupes:
        print("✅ No duplicates found")
        return
    
    total_waste = 0
    group_num = 0
    for h, group in sorted(dupes.items(), key=lambda x: -x[1][0][1]):
        group_num += 1
        size = group[0][1]
        waste = size * (len(group) - 1)
        total_waste += waste
        print(f"📁 Group {group_num} ({fmt_size(size)} each, {len(group)} copies, {fmt_size(waste)} wasted):")
        for path, _ in group:
            print(f"   {os.path.relpath(path, root)}")
        print()
    
    print(f"{'='*50}")
    print(f"📊 {group_num} duplicate group(s)")
    print(f"💾 {fmt_size(total_waste)} could be reclaimed")

def cmd_json(args):
    root = args[0] if args and not args[0].startswith("-") else "."
    dupes = scan(os.path.abspath(root))
    output = []
    for h, group in dupes.items():
        output.append({"hash": h, "size": group[0][1], "files": [p for p, _ in group]})
    print(json.dumps(output, indent=2))

CMDS = {"find":cmd_find,"f":cmd_find,"json":cmd_json}

if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or args[0] in ("-h","--help"):
        print("dupefind - Find duplicate files by content")
        print("Commands: find [dir] [--min bytes] [--ext .py,.js], json [dir]")
        sys.exit(0)
    cmd = args[0]
    if cmd in CMDS: CMDS[cmd](args[1:])
    else: cmd_find(args)
