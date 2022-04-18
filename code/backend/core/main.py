import os
import json
import zipfile
from core.CollaborER_wrapper import CollaborER_have_fun
from core.EASY_wrapper import EASY_have_fun
from core.LargeEA_wrapper import LargeEA_have_fun
from core.utils import get_result_for_frontend
from core.utils import getTaskLogger, init_task_logger

def unzip_files(file_path: str, extra_path: str):
    if not os.path.exists(extra_path):
        os.mkdir(extra_path)
        z_f = zipfile.ZipFile(file_path + ".zip", "r")
        for f in z_f.namelist():
            z_f.extract(f, extra_path)
        z_f.close()

def er_with_table_or_graph(task_id: str):
    # {project_path}/data/{task_id}/
    task_path = os.path.join(os.getcwd(), "data", task_id)
    data_path = os.path.join(task_path, "dataset")
    # logger = getTaskLogger(task_path)
    logger = init_task_logger(task_id)
    with open(os.path.join(task_path, "config.json"), "r") as rd:
        config = json.load(rd)
    logger.info(f"config: {str(config)}")
    with open(os.path.join(task_path, "gnn_config.json"), "r") as rd:
        gnn_config = json.load(rd)
    logger.info(f"gnn_config: {str(gnn_config)}")
    if "data_type" in config.keys():
        tp = config["data_type"]
        if tp == "table":
            CollaborER_have_fun(logger, task_path, data_path, config, gnn_config)
            get_result_for_frontend(task_path=task_path, data_type="table", pair=config["pair"])
        elif tp == "graph":
            er_model = config["er_model"]
            if er_model == "EASY":
                EASY_have_fun(logger, task_path, data_path, config, gnn_config)
                get_result_for_frontend(task_path=task_path, data_type="graph", pair=config["pair"],
                                        srprs=(config["pair"] in ["en_de", "en_fr"]))
            else:
                LargeEA_have_fun(logger, task_path, data_path, config, gnn_config)
                get_result_for_frontend(task_path=task_path, data_type="graph", pair=config["pair"],
                                        srprs=False, largeEA=True)
        elif tp == "table_graph":
            er_model = config["er_model"]
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
            if er_model == "EASY":
                EASY_have_fun(logger, task_path, data_path, config, gnn_config)
                get_result_for_frontend(task_path=task_path, data_type="graph", pair=config["pair"],
                                        srprs=True, table_graph=True)
            else:
                LargeEA_have_fun(logger, task_path, data_path, config, gnn_config)
                get_result_for_frontend(task_path=task_path, data_type="graph", pair=config["pair"],
                                        srprs=False, largeEA=True, table_graph=True)
        else:
            logger.error("Unsupported Data Type: %s", tp)
        logger.info("END")
    else:
        logger.error("Data Type Must be Given")
    # FOR DEMO TEST
    log_list = []
    with open(os.path.join(task_path, "task.log"), "r") as rd:
        for line in rd.readlines():
            log_list.append(line)
    with open(os.path.join(task_path, "logs.json"), "w") as wt:
        json.dump(log_list, wt)