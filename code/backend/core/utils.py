import hashlib
import logging
import json
import os
import shutil
from typing import List, Dict
from loguru import logger
import numpy as np
from core.entity_resolution.EASY.utils import readobj


def task_md5_hash(task_path: str) -> str:
    # hash without ground_truth
    # table/triples test/ent_links config,gnn_config
    md5 = hashlib.md5()
    for root, dirs, files in os.walk(task_path):
        for file in files:
            if file == "test.csv" or file == "ent_links" or file == "task.log" or file == "meta.json" or file =="dataset.zip":
                continue
            file_name = os.path.join(root, file)
            if file == "config.json" or file == "gnn_config.json":
                print(file_name)
                with open(file_name, "rb") as rd:
                    data:Dict = json.load(rd)
                    keys=sorted(data.keys())
                    for key in keys:
                        md5.update(str(data[key]).encode("utf-8"))
            else:
                print(file_name)
                with open(file_name, "rb") as rd:
                    while True:
                        buf = rd.read(4096)
                        if not buf:
                            break
                        md5.update(buf)
    return md5.hexdigest()


def has_pretrained_model(md5: str) -> bool:
    path = os.path.join(os.getcwd(), "pretrained", md5)
    if os.path.exists(path):
        if os.path.exists(f"{path}/final_model.pt"):
            return True
        else:
            shutil.rmtree(path)
            return False
    else:
        return False;

def init_task_logger(task_id: str):
    task_logger = logger.bind(task=task_id)
    task_path = os.path.join(os.getcwd(), "data", task_id)
    logger.add(os.path.join(task_path, "task.log"),
        format='<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <level>{message}</level>',
        filter=lambda x: x["extra"]["task"] == task_id)
    return task_logger


def getTaskLogger(task_path: str) -> logging.Logger:
    logger = logging.getLogger(task_path)
    if logger.hasHandlers():
        return logger
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | [%(filename)s:%(lineno)d] | %(message)s")
    c_handler = logging.StreamHandler()
    c_handler.setLevel(logging.INFO)
    c_handler.setFormatter(formatter)
    logger.addHandler(c_handler)
    f_handler = logging.FileHandler("{0}/task.log".format(task_path), mode="a")
    f_handler.setLevel(logging.INFO)
    f_handler.setFormatter(formatter)
    logger.addHandler(f_handler)
    logger.setLevel(logging.INFO)
    return logger


def get_result_for_frontend(task_path: str, data_type: str, pair: str, srprs=False, largeEA=False, table_graph=False):
    """
            input: result.csv (u\tv\n)
            output:
                    result_columns.json
                    result_data.json
                    result_categories.json
                    result_left_edges.json
                    result_right_edges.json
                    """
    data_path = os.path.join(task_path, "dataset")
    lang_sr, lang_tg = pair.split("_")
    assert data_type in ["table", "graph"]
    if data_type == "table":
        columns = []
        atts = []
        categories = [
            {"name": "entity"},
            {"name": "value"},
        ]
        left_edges = []
        right_edges = []
        data = []
        et_cnt = 1
        left_val_cnt = 1
        right_val_cnt = 1
        left_val_dic = {}
        right_val_dic = {}
        with open(os.path.join(data_path, "id2atts.txt"), "r") as rd:
            for line in rd.readlines():
                id, name = line.strip("\n").split("\t")
                atts.append(name)
        columns.append({"field": "A_id", "label": "id"})
        for att in atts:
            columns.append({"field": "A_" + att, "label": att})
        columns.append({"field": "align", "label": "", "centered": True})
        columns.append({"field": "B_id", "label": "id"})
        for att in atts:
            columns.append({"field": "B_" + att, "label": att})
        table_dic = [dict(), dict()]
        for idx, suf in enumerate([lang_sr, lang_tg]):
            with open(os.path.join(data_path, f"table_{suf}.csv"), "r") as rd:
                for line in rd.readlines()[1:]:
                    id = int(line.strip("\n").split(",")[0])
                    table_dic[idx][id] = line
        pairs = np.loadtxt(os.path.join(data_path, "result.txt"))
        for [id_a, id_b] in pairs:
            eA = table_dic[0][id_a]
            eB = table_dic[1][id_b]
            et_cnt += 1
            dt = {}
            dt["A_id"] = et_cnt
            for k, v in zip(atts, eA.strip("\n").split(",")[1:]):
                dt["A_" + k] = v
                if v != "":
                    if v not in left_val_dic.keys():
                        left_val_dic[v] = "A_V" + str(left_val_cnt)
                        left_val_cnt += 1
                    left_edges.append({
                        "source": "A_E" + str(et_cnt - 1),
                        "target": left_val_dic[v],
                        "type": k,
                    })
            dt["align"] = "<=>"
            dt["B_id"] = et_cnt
            for k, v in zip(atts, eB.strip("\n").split(",")[1:]):
                dt["B_" + k] = v
                if v != "":
                    if v not in right_val_dic.keys():
                        right_val_dic[v] = "B_V" + str(right_val_cnt)
                        right_val_cnt += 1
                    right_edges.append({
                        "source": "B_E" + str(et_cnt - 1),
                        "target": right_val_dic[v],
                        "type": k,
                    })
            data.append(dt)
        with open(os.path.join(task_path, "task.log"), "r") as rd:
            lines = rd.readlines()
            res = str(str(lines[-2]).strip().split("|")[2]).strip().split()
            p = float(res[2])
            r = float(res[4])
            f1 = float(res[6])
        with open(os.path.join(task_path, "meta.json"), "r") as rd:
            meta = json.load(rd)
            meta["precision"] = p
            meta["recall"] = r
            meta["f1-score"] = f1
        with open(os.path.join(task_path, "meta.json"), "w") as wt:
            json.dump(meta, wt)

        with open(os.path.join(data_path, "result_columns.json"), "w") as wt:
            wt.write(json.dumps(columns))
        with open(os.path.join(data_path, "result_data.json"), "w") as wt:
            wt.write(json.dumps(data))
        with open(os.path.join(data_path, "result_categories.json"), "w") as wt:
            wt.write(json.dumps(categories))
        with open(os.path.join(data_path, "result_left_edges.json"), "w") as wt:
            wt.write(json.dumps(left_edges))
        with open(os.path.join(data_path, "result_right_edges.json"), "w") as wt:
            wt.write(json.dumps(right_edges))
    elif data_type == "graph":
        columns = [
            {"field": "A_name", "label": "entity"},
            {"field": "align", "label": ""},
            {"field": "B_name", "label": "entity"},
        ]
        categories = [
            {"name": "entity"},
            {"name": "neighbor entity"}
        ]
        if srprs:
            ent1, ent2 = readobj(os.path.join(data_path, "ent_name2id"))
            data = []
            graphA_ls = dict()
            graphB_ls = dict()
            for key in ent1.keys():
                graphA_ls[ent1[key]] = key
            for key in ent2.keys():
                graphB_ls[ent2[key]] = key
            pairs = np.loadtxt(os.path.join(data_path, "result.txt"))
            for id_a, id_b in pairs:
                eA = str(graphA_ls[int(id_a)]).split("/")[-1]
                eB = str(graphB_ls[int(id_b)]).split("/")[-1]
                data.append({
                    "A_name": eA,
                    "align": "<=>",
                    "B_name": eB,
                })
            edgesA = dict()
            edgesB = dict()
            with open(os.path.join(data_path, f"triples_{lang_sr}"), "r") as rd:
                for line in rd.readlines():
                    u, r, v = str(line).strip("\n").split("\t")
                    if u not in ent1.keys() or v not in ent1.keys():
                        continue
                    u = ent1[u]
                    v = ent1[v]
                    if u not in edgesA.keys():
                        edgesA[u] = set()
                    edgesA[u].add(v)
                    if v not in edgesA.keys():
                        edgesA[v] = set()
                    edgesA[v].add(u)
            for key in edgesA.keys():
                edgesA[key] = list(edgesA[key])
            with open(os.path.join(data_path, f"triples_{lang_tg}"), "r") as rd:
                for line in rd.readlines():
                    u, r, v = str(line).strip("\n").split("\t")
                    u = ent2[u]
                    v = ent2[v]
                    if u not in edgesB.keys():
                        edgesB[u] = set()
                    edgesB[u].add(v)
                    if v not in edgesB.keys():
                        edgesB[v] = set()
                    edgesB[v].add(u)
            for key in edgesB.keys():
                edgesB[key] = list(edgesB[key])
            with open(os.path.join(data_path, "result_left_edges.json"), "w") as wt:
                wt.write(json.dumps(edgesA))
            with open(os.path.join(data_path, "result_right_edges.json"), "w") as wt:
                wt.write(json.dumps(edgesB))
            print(table_graph)
            if not table_graph:
                with open(os.path.join(task_path, "task.log"), "r") as rd:
                    lines = rd.readlines()
                    res = str(lines[-6]).strip().split(" | ")[2].strip().replace("'", "\"")
                    print(res)
                    js = json.loads(res)
                    hits_1 = js["hits@1"]
                    hits_5 = js["hits@5"]
                    mrr = js["MRR"]
                    with open(os.path.join(task_path, "meta.json"), "r") as rd:
                        meta = json.load(rd)
                        meta["hits@1"] = str(round(hits_1,4))
                        meta["hits@5"] = str(round(hits_5,4))
                        meta["mrr"] = str(round(mrr,4))
                    print(meta)
                    with open(os.path.join(task_path, "meta.json"), "w") as wt:
                        json.dump(meta, wt)
        elif largeEA:
            # TODO task.log 位置
            ent1, ent2 = readobj(os.path.join(data_path, "ent_name2id"))
            data = []
            graphA_ls = dict()
            graphB_ls = dict()
            for key in ent1.keys():
                graphA_ls[ent1[key]] = key
            for key in ent2.keys():
                graphB_ls[ent2[key]] = key
            pairs = np.loadtxt(os.path.join(data_path, "result.txt"))
            for id_a, id_b in pairs:
                eA = str(graphA_ls[int(id_a)]).split("/")[-1]
                eB = str(graphB_ls[int(id_b)]).split("/")[-1]
                data.append({
                    "A_name": eA,
                    "align": "<=>",
                    "B_name": eB,
                })
            edgesA = dict()
            edgesB = dict()
            with open(os.path.join(data_path, f"triples_{lang_sr}"), "r") as rd:
                for line in rd.readlines():
                    u, r, v = str(line).strip("\n").split("\t")
                    u = ent1[u]
                    v = ent1[v]
                    if u not in edgesA.keys():
                        edgesA[u] = set()
                    edgesA[u].add(v)
                    if v not in edgesA.keys():
                        edgesA[v] = set()
                    edgesA[v].add(u)
            for key in edgesA.keys():
                edgesA[key] = list(edgesA[key])
            with open(os.path.join(data_path, f"triples_{lang_tg}"), "r") as rd:
                for line in rd.readlines():
                    u, r, v = str(line).strip("\n").split("\t")
                    u = ent2[u]
                    v = ent2[v]
                    if u not in edgesB.keys():
                        edgesB[u] = set()
                    edgesB[u].add(v)
                    if v not in edgesB.keys():
                        edgesB[v] = set()
                    edgesB[v].add(u)
            for key in edgesB.keys():
                edgesB[key] = list(edgesB[key])
            with open(os.path.join(data_path, "result_left_edges.json"), "w") as wt:
                wt.write(json.dumps(edgesA))
            with open(os.path.join(data_path, "result_right_edges.json"), "w") as wt:
                wt.write(json.dumps(edgesB))
            with open(os.path.join(task_path, "task.log"), "r") as rd:
                lines = rd.readlines()
                res = str(lines[-2]).strip().split(" | ")[2].strip().split("-")[1].strip()[8:].replace("'", "\"")
                print(res)
                js = json.loads(res)
                hits_1 = js["hits@1"]
                hits_5 = js["hits@5"]
                mrr = js["MRR"]
                with open(os.path.join(task_path, "meta.json"), "r") as rd:
                    meta = json.load(rd)
                    meta["hits@1"] = str(round(hits_1, 4))
                    meta["hits@5"] = str(round(hits_5, 4))
                    meta["mrr"] = str(round(mrr, 4))
                with open(os.path.join(task_path, "meta.json"), "w") as wt:
                    json.dump(meta, wt)
        else:
            data = []
            graphA_ls = []
            graphB_ls = []
            id2idxA = dict()
            id2idxB = dict()
            with open(os.path.join(data_path, f"ent_ids_{lang_sr}"), "r") as rd:
                i = 0
                for line in rd.readlines():
                    id = int(str(line.strip("\n")).split("\t")[0])
                    name = str(line.strip("\n").split('/')[-1])
                    id2idxA[id] = i
                    graphA_ls.append(name)
                    i += 1
            with open(os.path.join(data_path, f"ent_ids_{lang_tg}"), "r") as rd:
                i = 0
                for line in rd.readlines():
                    id = int(str(line.strip("\n")).split("\t")[0])
                    name = str(line.strip("\n").split('/')[-1])
                    id2idxB[id] = i
                    graphB_ls.append(name)
                    i += 1
            pairs = np.loadtxt(os.path.join(data_path, "result.txt"))
            for id_a, id_b in pairs:
                eA = graphA_ls[int(id_a)]
                eB = graphB_ls[int(id_b)]
                data.append({
                    "A_name": eA,
                    "align": "<=>",
                    "B_name": eB,
                })
            edgesA = dict()
            edgesB = dict()
            with open(os.path.join(data_path, f"triples_{lang_sr}"), "r") as rd:
                for line in rd.readlines():
                    u, r, v = list(map(int, str(line).strip("\n").split("\t")))
                    u = id2idxA[u]
                    v = id2idxA[v]
                    if u not in edgesA.keys():
                        edgesA[u] = set()
                    edgesA[u].add(v)
                    if v not in edgesA.keys():
                        edgesA[v] = set()
                    edgesA[v].add(u)
            for key in edgesA.keys():
                edgesA[key] = list(edgesA[key])
            with open(os.path.join(data_path, f"triples_{lang_tg}"), "r") as rd:
                for line in rd.readlines():
                    u, r, v = list(map(int, str(line).strip("\n").split("\t")))
                    u = id2idxB[u]
                    v = id2idxB[v]
                    if u not in edgesB.keys():
                        edgesB[u] = set()
                    edgesB[u].add(v)
                    if v not in edgesB.keys():
                        edgesB[v] = set()
                    edgesB[v].add(u)
            for key in edgesB.keys():
                edgesB[key] = list(edgesB[key])
            with open(os.path.join(data_path, "result_left_edges.json"), "w") as wt:
                wt.write(json.dumps(edgesA))
            with open(os.path.join(data_path, "result_right_edges.json"), "w") as wt:
                wt.write(json.dumps(edgesB))
            with open(os.path.join(task_path, "task.log"), "r") as rd:
                lines = rd.readlines()
                res = str(lines[-6]).strip().split(" | ")[2].strip().split("-")[1].strip().replace("'", "\"")
                print(res)
                js = json.loads(res)
                hits_1 = js["hits@1"]
                hits_5 = js["hits@5"]
                mrr = js["MRR"]
                with open(os.path.join(task_path, "meta.json"), "r") as rd:
                    meta = json.load(rd)
                    meta["hits@1"] = str(round(hits_1, 4))
                    meta["hits@5"] = str(round(hits_5, 4))
                    meta["mrr"] = str(round(mrr, 4))
                with open(os.path.join(task_path, "meta.json"), "w") as wt:
                    json.dump(meta, wt)
    with open(os.path.join(data_path, "result_columns.json"), "w") as wt:
        wt.write(json.dumps(columns))
    with open(os.path.join(data_path, "result_data.json"), "w") as wt:
        wt.write(json.dumps(data))
    with open(os.path.join(data_path, "result_categories.json"), "w") as wt:
        wt.write(json.dumps(categories))
