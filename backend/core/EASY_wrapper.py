from __future__ import annotations
import os
from collections import OrderedDict
import loguru
import numpy
import numpy as np
import pickle5
import torch.cuda
from tqdm import tqdm
from core.utils import task_md5_hash, has_pretrained_model
from core.entity_resolution.EASY.neap_wrapper import neap_main
from core.entity_resolution.EASY.main_wrapper import main_main


def EASY_have_fun(
        logger: loguru.Logger,
        task_path: str,
        data_path: str,
        config: dict,
        gnn_config: dict,
):
    seed = int(config["seed"])
    os.environ['MKL_THREADING_LAYER'] = 'GNU'
    import random
    import numpy as np
    import torch
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    os.environ['PYTHONHASHSEED'] = str(seed)

    clean = bool(config["clean"])
    pair = str(config["pair"])
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(device)
    gnn_model = config["gnn_model"]
    gnn_epoch = int(gnn_config["epoch"])
    iteration = int(config["iteration"])

    md5 = task_md5_hash(task_path)
    pretrained = has_pretrained_model(md5)
    print(f"md5: {md5}")

    _eval=config["data_type"]!="table_graph"

    logger.info("Start [neap]")
    neap_main(logger=logger, pretrained=pretrained, md5=md5, task_path=task_path, pair=pair, device=device,_eval=_eval)
    logger.info("End [neap]")

    logger.info("Start [srs]")
    main_main(logger=logger, pretrained=pretrained, md5=md5,task_path=task_path, seed=seed, pair=pair,
              model=gnn_model, epoch=gnn_epoch, n_it=iteration,_eval=_eval)
    logger.info("End [srs]")
