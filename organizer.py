import json
import os
import sys
import time

from collections import namedtuple
from contextlib import suppress
from os import path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


class EventHandler(FileSystemEventHandler):
    def __init__(self, dest_dir, exts_dirs):
        self.dest_dir = dest_dir
        self.exts_dirs = exts_dirs

    def on_modified(self, event):
        if event.is_directory: return

        filename = path.basename(event.src_path)

        if filename.startswith("_"): return

        extension = path.splitext(filename)[1]
        ext_dir = self.exts_dirs.get(extension, self.exts_dirs["other"])

        dest_dir = self.dest_dir

        for part in path.normcase(ext_dir).split("\\"):
                dest_dir = path.join(dest_dir, part)
                with suppress(OSError):
                    os.mkdir(dest_dir)

        full_file_path =  path.join(dest_dir, filename)

        try:
            os.replace(event.src_path, full_file_path)
        except OSError:
            pass

Dir_pair = namedtuple("Dir_pair", ["watched", "destination"])

with open("config.json") as f:
    config = json.load(f)

watched_dirs_cfgs = config["watched_dirs_cfgs"]

observers = []

for cfg in watched_dirs_cfgs:
    watched_dirs, destination_dirs = cfg["watched_dirs"], cfg["destination_dirs"]
    extension_dirs = cfg["extension_dirs"]
    if len(watched_dirs) > len(destination_dirs):
        destination_dirs += [destination_dirs[-1] for i in
                                range(len(watched_dirs) - len(destination_dirs))]

    dir_pairs = [Dir_pair(d1, d2) for d1, d2 in zip(watched_dirs, destination_dirs)]

    for pair in dir_pairs:
        observer = Observer()
        handler = EventHandler(pair.destination, extension_dirs)
        observer.schedule(handler, pair.watched)
        observers.append(observer)

for o in observers: o.start()

try:
    while True:
        time.sleep(3)
except KeyboardInterrupt:
    for o in observers: o.stop()

for o in observers: o.join()