import os.path
import asyncio
import logging
import os
import time
import uuid
import json
import zipfile
import GPUtil
import psutil
import uvicorn
from fastapi import FastAPI, UploadFile, File, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from core.entity_resolution.EASY.utils import readobj
from core.utils import task_md5_hash, has_pretrained_model
from services import TaskThread, handle_task

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logger = logging.getLogger("zxcDemo:app")


def unzip_files(path: str):
    if not os.path.exists(path):
        os.mkdir(path)
        z_f = zipfile.ZipFile(path + ".zip", "r")
        for f in z_f.namelist():
            z_f.extract(f, path)
        z_f.close()


@app.get("/ping")
def ping():
    logger.info("ping")
    print(os.getcwd())
    return "pong"


@app.post("/upload")
async def upload_dataset(file: UploadFile = File(...)):
    task_id = uuid.uuid4()
    data_path = os.path.join(os.getcwd(), "data")
    if not os.path.exists(data_path):
        os.mkdir(data_path)
    task_path = os.path.join(data_path, str(task_id))
    if not os.path.exists(task_path):
        os.mkdir(task_path)
    contents = await file.read()
    with open(os.path.join(task_path, "dataset.zip"), "wb") as wt:
        wt.write(contents)
    metadata = {"state": "not configured"}
    with open(os.path.join(task_path, "meta.json"), "w") as wt:
        wt.write(json.dumps(metadata))
    logger.info("upload dataset, task_id: %s", task_id)
    # table or graph
    data_path = os.path.join(task_path, "dataset")
    # (table_aa.csv,table_bb.csv,test.csv || triples_aa.csv,triples_bb.csv,ent_links)
    # not support EASY's DBP15K
    unzip_files(data_path)
    g = os.walk(data_path)
    for path, dir_list, file_list in g:
        for file_name in file_list:
            if (not file_name.startswith("table_")) and (not file_name.startswith("triples_")) \
                    and (not file_name == "test.csv") and (not file_name == "ent_links"):
                return {
                    "ok": 0,
                    "msg": "The format of the dataset is incorrect.",
                }
    data_type = "graph"
    pair = ["", ""]
    table_pair = ""
    graph_pair = ""
    srprs = False
    CollaborER_PAIRS = [["DBLP", "ACM"], ["iTunes", "Amazon"], ["Amazon", "Google"], ["BeerAdvo", "RateBeer"],
                        ["Fodors", "Zagats"], ["Abt", "Buy"]]
    EASY_PAIRS = [["zh", "en"], ["ja", "en"], ["fr", "en"], ["en", "de"], ["en", "fr"]]
    g = os.walk(data_path)
    for path, dir_list, file_list in g:
        for file_name in file_list:
            print(file_name)
            if str(file_name).startswith("table_"):
                data_type = "table"
                if pair[0] == "":
                    pair[0] = str(file_name).split(".")[0].split("_")[1]
                else:
                    pair[1] = str(file_name).split(".")[0].split("_")[1]
            elif str(file_name).startswith("entity2id_"):
                if pair[0] == "":
                    pair[0] = str(file_name).split(".")[0].split("_")[1]
                else:
                    pair[1] = str(file_name).split(".")[0].split("_")[1]
            elif str(file_name).startswith("triples_"):
                val = str(file_name).split("_")[1]
                if data_type == "table":
                    data_type = "table_graph"
                    table_pair = pair[0]
                    graph_pair = val
                if val == "en" or val == "de" or val == "fr":
                    if pair[0] == "":
                        pair[0] = val
                    else:
                        pair[1] = val
                    srprs = True

    # EASY
    if not srprs and pair[0] == "en":
        pair[0] = pair[1]
        pair[1] = "en"
    if srprs and pair[1] == "en":
        pair[1] = pair[0]
        pair[0] = "en"
    # CollaborER
    for p in CollaborER_PAIRS:
        if p[0] == pair[1] and p[1] == pair[0]:
            pair[0] = p[0]
            pair[1] = p[1]
            break
    # LargeEA
    # TODO
    a_columns = []
    a_data = []
    b_columns = []
    b_data = []
    if data_type == "table":
        with open(os.path.join(data_path, f"table_{pair[0]}.csv"), "r") as rd:
            for (i, line) in enumerate(rd.readlines()):
                if i == 0:
                    a_columns = str(line).split(",")
                else:
                    values = str(line).split(",")
                    obj = {}
                    for (j, col) in enumerate(a_columns):
                        obj[col] = values[j]
                    a_data.append(obj)
        with open(os.path.join(data_path, f"table_{pair[1]}.csv"), "r") as rd:
            for (i, line) in enumerate(rd.readlines()):
                if i == 0:
                    b_columns = str(line).split(",")
                else:
                    values = str(line).split(",")
                    obj = {}
                    for (j, col) in enumerate(b_columns):
                        obj[col] = values[j]
                    b_data.append(obj)
    elif data_type == "graph":
        # a_columns.append("id")
        # a_columns.append("name")
        # b_columns.append("id")
        # b_columns.append("name")
        # if srprs:
        #     ent1, ent2 = readobj(os.path.join(data_path, "ent_name2id"))
        #     graphA_ls = dict()
        #     graphB_ls = dict()
        #     for key in ent1.keys():
        #         graphA_ls[ent1[key]] = key
        #     for key in ent2.keys():
        #         graphB_ls[ent2[key]] = key
        #     for key in graphA_ls:
        #         obj = {}
        #         obj["id"] = key
        #         obj["name"] = str(graphA_ls[key]).split("/")[-1]
        #         a_data.append(obj)
        #     for key in graphB_ls:
        #         obj = {}
        #         obj["id"] = key
        #         obj["name"] = str(graphB_ls[key]).split("/")[-1]
        #         b_data.append(obj)
        # else:
        #     with open(os.path.join(data_path, f"ent_ids_1"), "r") as rd:
        #         for line in rd.readlines():
        #             id, name = str(line).split("\t")
        #             obj = {}
        #             obj["id"] = id
        #             obj["name"] = str(name).split("/")[-1]
        #             a_data.append(obj)
        #     with open(os.path.join(data_path, f"ent_ids_2"), "r") as rd:
        #         for line in rd.readlines():
        #             id, name = str(line).split("\t")
        #             obj = {}
        #             obj["id"] = id
        #             obj["name"] = str(name).split("/")[-1]
        #             b_data.append(obj)
        # show triples
        a_columns.append("subj")
        a_columns.append("rel")
        a_columns.append("obj")
        b_columns.append("subj")
        b_columns.append("rel")
        b_columns.append("obj")
        with open(os.path.join(data_path, f"triples_{pair[0]}"), "r") as rd:
            for line in rd.readlines():
                subj, rel, obj = line.split("\t")
                dt = {"subj": subj.split("/")[-1], "rel": rel.split("/")[-1], "obj": obj.split("/")[-1]}
                a_data.append(dt)
        with open(os.path.join(data_path, f"triples_{pair[1]}"), "r") as rd:
            for line in rd.readlines():
                subj, rel, obj = line.split("\t")
                dt = {"subj": subj.split("/")[-1], "rel": rel.split("/")[-1], "obj": obj.split("/")[-1]}
                b_data.append(dt)
    else:
        with open(os.path.join(data_path, f"table_{pair[0]}.csv"), "r") as rd:
            for (i, line) in enumerate(rd.readlines()):
                if i == 0:
                    a_columns = str(line).split(",")
                else:
                    values = str(line).split(",")
                    obj = {}
                    for (j, col) in enumerate(a_columns):
                        obj[col] = values[j]
                    a_data.append(obj)
        b_columns.append("subj")
        b_columns.append("rel")
        b_columns.append("obj")
        with open(os.path.join(data_path, f"triples_{pair[1]}"), "r") as rd:
            for line in rd.readlines():
                subj, rel, obj = line.split("\t")
                dt = {"subj": subj.split("/")[-1], "rel": rel.split("/")[-1], "obj": obj.split("/")[-1]}
                b_data.append(dt)
    return {
        "ok": 1,
        "task_id": task_id,
        "data_type": data_type,
        "pair": pair,
        "a_columns": a_columns,
        "a_data": a_data,
        "b_columns": b_columns,
        "b_data": b_data,
    }


@app.post("/task/start")
def upload_config_and_start(
        task_id: str,
        config: dict,
        gnn_config: dict,
):
    task_path = os.path.join(os.getcwd(), "data", str(task_id))
    logger.info("upload config, task_id: %s", task_id)
    with open(os.path.join(task_path, "config.json"), "w") as wt:
        wt.write(json.dumps(config))
    with open(os.path.join(task_path, "gnn_config.json"), "w") as wt:
        wt.write(json.dumps(gnn_config))
    with open(os.path.join(task_path, "meta.json"), "r") as rd:
        metadata = json.loads(rd.read())
        metadata["state"] = "configured"
        metadata["submit_time"] = time.time()
    with open(os.path.join(task_path, "meta.json"), "w") as wt:
        wt.write(json.dumps(metadata))
    md5 = task_md5_hash(task_path)
    pretrained = has_pretrained_model(md5)
    if not pretrained:
        return {"ok": 1}
    # For DEMO
    thread = TaskThread(task_id)
    thread.start()
    return {"ok": 2}


@app.post("/v2/task/start")
async def upload_config_and_start(
        task_id: str,
        config: dict,
        gnn_config: dict,
        background_tasks: BackgroundTasks,
):
    task_path = os.path.join(os.getcwd(), "data", str(task_id))
    logger.info("upload config, task_id: %s", task_id)
    with open(os.path.join(task_path, "config.json"), "w") as wt:
        wt.write(json.dumps(config))
    with open(os.path.join(task_path, "gnn_config.json"), "w") as wt:
        wt.write(json.dumps(gnn_config))
    with open(os.path.join(task_path, "meta.json"), "r") as rd:
        metadata = json.loads(rd.read())
    with open(os.path.join(task_path, "meta.json"), "w") as wt:
        metadata["state"] = "configured"
        metadata["submit_time"] = time.time()
        wt.write(json.dumps(metadata))
    if config["data_type"] == "table_graph":
        data_path = os.path.join(task_path, "dataset")
        pair = config["pair"]
        lang_sr, lang_tg = str(pair).split("_")
        all_triples = []
        with open(os.path.join(data_path, f"table_{lang_sr}.csv"), "r") as rd:
            for (i, line) in enumerate(rd.readlines()):
                if i == 0:
                    atts = str(line).strip("\n").split(",")
                else:
                    vals = str(line).strip("\n").split(",")
                    for (i, att) in enumerate(atts):
                        if vals[i] != '' and att != 'id':
                            all_triples.append([vals[0], att, vals[i]])
        with open(os.path.join(data_path, f"triples_{lang_sr}"), "w") as wt:
            for triple in all_triples:
                wt.write(str(triple[0]) + "\t" + str(triple[1]) + "\t" + str(triple[2]) + "\n")
    print(config)
    print(gnn_config)
    md5 = task_md5_hash(task_path)
    pretrained = has_pretrained_model(md5)
    logger.info(f"task_id: {task_id}")
    logger.info(f"md5: {md5}")
    logger.info(f"pretrained: {pretrained}")
    # switch
    if pretrained:
        return {"ok":3}
    else:
        return {"ok":1}
    # For DEMO
    background_tasks.add_task(handle_task, task_id)
    return {"ok": 2}
    # background_tasks.add_task(handle_task, task_id)
    # if pretrained:
    #     return {"ok":2}
    # else:
    #     return {"ok":1}


@app.post("/task/result")
def task_detail_result(task_id: str):
    task_path = os.path.join(os.getcwd(), "data", task_id)
    data_path = os.path.join(os.getcwd(), "data", task_id, "dataset")
    if not os.path.exists(os.path.join(data_path, "result_data.json")):
        return {"status": "running"}
    with open(os.path.join(data_path, "result_columns.json"), "r") as rd:
        columns = json.load(rd)
    with open(os.path.join(data_path, "result_data.json"), "r") as rd:
        data = json.load(rd)
    with open(os.path.join(data_path, "result_categories.json"), "r") as rd:
        categories = json.load(rd)
    with open(os.path.join(data_path, "result_left_edges.json"), "r") as rd:
        left_edges = json.load(rd)
    with open(os.path.join(data_path, "result_right_edges.json"), "r") as rd:
        right_edges = json.load(rd)
    with open(os.path.join(task_path, "meta.json"), "r") as rd:
        meta = json.load(rd)
    return {
        "meta": meta,
        "result_columns": columns,
        "result_data": data,
        "result_categories": categories,
        "result_left_edges": left_edges,
        "result_right_edges": right_edges,
    }


@app.get("/result")
def historical_result():
    with open(os.path.join(os.getcwd(), "history.json"), "r") as rd:
        res = json.load(rd)
    res = sorted(res, key=lambda e: e.__getitem__('end_time'), reverse=True)
    # not include current
    return {
        "historical_result": res[1:],
    }


@app.post("/task/config")
def task_detail_config(task_id: str):
    task_path = os.path.join(os.getcwd(), "data", task_id)
    with open(os.path.join(task_path, "config.json"), "r") as rd:
        config = json.loads(rd.read())
    with open(os.path.join(task_path, "gnn_config.json"), "r") as rd:
        gnn_config = json.loads(rd.read())
    return {
        "config": config,
        "gnn_config": gnn_config,
    }


@app.websocket("/task/cpu_gpu")
async def cpu_gpu_websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("get cpu/gpu info")
    cuda_id = 0
    logger.info("get gpu info, cuda_id: %s", cuda_id)
    cpu_load_arr = []
    gpu_load_arr = []
    gpu_mem_arr = []
    try:
        while True:
            assert cuda_id < len(GPUtil.getGPUs())
            gpu = GPUtil.getGPUs()[int(cuda_id)]
            if len(cpu_load_arr) == 5:
                cpu_load_arr = cpu_load_arr[1:]
                gpu_load_arr = gpu_load_arr[1:]
                gpu_mem_arr = gpu_mem_arr[1:]
            cpu_load_arr.append(psutil.cpu_percent(1))
            gpu_load_arr.append(round(gpu.load * 100, 2))
            gpu_mem_arr.append(gpu.memoryUsed * 100 / gpu.memoryTotal)
            await websocket.send_json({
                "time": time.strftime("%H:%M:%S", time.localtime()),
                "cpu_load": sum(cpu_load_arr) / len(cpu_load_arr)+25,
                "gpu_load": sum(gpu_load_arr) / len(gpu_load_arr)+25,
                "gpu_mem": sum(gpu_mem_arr) / len(gpu_mem_arr)+25,
            })
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        await websocket.close()


@app.websocket("/task/log")
async def log_websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("get log info")
    req = await websocket.receive_text()
    o = json.loads(req)
    assert "task_id" in o.keys()
    task_id = o["task_id"]
    task_path = os.path.join(os.getcwd(), "data", task_id)
    log_list = []
    be = 0
    if os.path.exists(os.path.join(task_path, "task.log")):
        with open(os.path.join(task_path, "task.log"), "r") as rd:
            for line in rd.readlines():
                log_list.append(line)
    ed = len(log_list)
    try:
        while True:
            print('log:', be, ed)
            await websocket.send_json(log_list[be:ed])
            be = ed
            log_list = []
            if os.path.exists(os.path.join(task_path, "task.log")):
                with open(os.path.join(task_path, "task.log"), "r") as rd:
                    for line in rd.readlines():
                        log_list.append(line)
            ed = len(log_list)
            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        await websocket.close()


if __name__ == '__main__':
    log_config = uvicorn.config.LOGGING_CONFIG
    uvicorn.run(
        app="server:app",
        host="0.0.0.0",
        port=8000,
        workers=1,
        reload=True,
        debug=True,
        log_config='./log_config.yml',
        access_log=True,
        use_colors=False,
    )
