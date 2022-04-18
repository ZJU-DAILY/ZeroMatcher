import logging
import os
import threading
import json
import time
import zipfile
from typing import List
from core.main import er_with_table_or_graph

logger = logging.getLogger("zxcDemo:app")


def handle_task(task_id: str):
    task_path = os.path.join(os.getcwd(), "data", task_id)
    if not os.path.exists(task_path):
        print(task_path)
        logger.error("no this task, task_id: %s", task_id)
        return
    logger.info("start a task, task_id: %s", task_id)
    if os.path.exists(os.path.join(task_path, 'task.log')):
        os.remove(os.path.join(task_path, 'task.log'))
    with open(os.path.join(task_path, "meta.json"), "r") as rd:
        meta = json.loads(rd.read())
    meta["state"] = "running"
    meta["start_time"] = time.time()
    with open(os.path.join(task_path, "meta.json"), "w") as wt:
        wt.write(json.dumps(meta))
    # data clean and entity resolution
    er_with_table_or_graph(task_id)
    with open(os.path.join(task_path, "meta.json"), "r") as rd:
        meta = json.loads(rd.read())
    meta["complete_time"] = time.time()
    meta["state"] = "completed"
    with open(os.path.join(task_path, "meta.json"), "w") as wt:
        wt.write(json.dumps(meta))
    with open(os.path.join(task_path, "config.json"), "r") as rd:
        config = json.load(rd)
    with open(os.path.join(task_path, "gnn_config.json"), "r") as rd:
        gnn_config = json.load(rd)
    with open(os.path.join(os.getcwd(), "history.json"), "r") as rd:
        history: List = json.load(rd)
    curr = {
        "dataset": config["pair"],
        "data_type": config["data_type"],
        "er_model": config["er_model"],
        "gnn_model": config["gnn_model"],
        "end_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(meta["complete_time"])),
        "run_time": str(round(meta["complete_time"] - meta["start_time"], 1))+"s",
        "config": config,
        "gnn_config": gnn_config
    }
    if "precision" in meta:
        curr["precision"] = meta["precision"]
    if "recall" in meta:
        curr["recall"] = meta["recall"]
    if "f1-score" in meta:
        curr["f1"] = meta["f1-score"]
    if "hits@1" in meta:
        curr["hits_1"] = meta["hits@1"]
    if "hits@5" in meta:
        curr["hits_5"] = meta["hits@5"]
    if "mrr" in meta:
        curr["mrr"] = meta["mrr"]
    history.append(curr)
    with open(os.path.join(os.getcwd(), "history.json"), "w") as wt:
        json.dump(history, wt)
    logger.info("end a task, task_id: %s", task_id)


class TaskThread(threading.Thread):
    def __init__(self, task_id: str):
        threading.Thread.__init__(self)
        self.task_id = task_id

    def run(self):
        # setRunning(True)
        handle_task(self.task_id)
        # setRunning(False)
