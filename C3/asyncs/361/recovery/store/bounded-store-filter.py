#!/usr/bin/env python3
import re
import sys

ids_path, log_path = sys.argv[1:3]
with open(ids_path, encoding="ascii") as handle:
    activation_ids = {line.strip() for line in handle if line.strip()}
tid_re = re.compile(r"\[#([^]]+)\]")
activation_re = re.compile(r"saving document: 'id: [^/]+/([^,']+)")
selected_tids = set()
with open(log_path, encoding="utf-8", errors="replace") as handle:
    for line in handle:
        if "database_saveDocument_start" in line:
            activation = activation_re.search(line)
            tid = tid_re.search(line)
            if activation and tid and activation.group(1) in activation_ids:
                selected_tids.add(tid.group(1))
                sys.stdout.write(line)
            continue
        if "database_saveDocument_finish" in line:
            tid = tid_re.search(line)
            if tid and tid.group(1) in selected_tids:
                sys.stdout.write(line)
