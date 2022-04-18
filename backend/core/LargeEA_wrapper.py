from __future__ import annotations
import os
import loguru
from core.entity_resolution.LargeEA.main_wrapper import main_main
from core.utils import task_md5_hash, has_pretrained_model


def LargeEA_have_fun(
        logger: loguru.Logger,
        task_path: str,
        data_path: str,
        config: dict,
        gnn_config: dict,
):
    md5 = task_md5_hash(task_path)
    pretrained = has_pretrained_model(md5)
    md5_path = os.path.join(os.getcwd(), "pretrained", md5)
    print(f"md5: {md5}")
    # name channel
    # phase 1
    pair = config["pair"]
    logger.info("Start [phase 1]")
    if pretrained:
        with open(os.path.join(md5_path, "bert_result"), "rb") as rd:
            data = rd.read()
        with open(os.path.join(data_path, "bert_result"), "wb") as wt:
            wt.write(data)
    else:
        main_main(logger, pretrained, md5, task_path, pair, phase=1)
    logger.info("End [phase 1]")
    # phase 2
    logger.info("Start [phase 2]")
    # main_main(logger, pretrained, md5, task_path, pair, phase=2)
    if pretrained:
        with open(os.path.join(md5_path, "sim_phase_2"), "rb") as rd:
            data = rd.read()
        with open(os.path.join(data_path, "sim_phase_2"), "wb") as wt:
            wt.write(data)
    else:
        main_main(logger, pretrained, md5, task_path, pair, phase=2)
    logger.info("End [phase 2]")
    # phase 3
    logger.info("Start [phase 3]")
    if pretrained:
        with open(os.path.join(md5_path, "sim_phase_3"), "rb") as rd:
            data = rd.read()
        with open(os.path.join(data_path, "sim_phase_3"), "wb") as wt:
            wt.write(data)
    else:
        main_main(logger, pretrained, md5, task_path, pair, phase=3)
    logger.info("End [phase 3]")

    # structure channel
    # phase 0
    logger.info("Start [phase 0]")
    pretrained=False
    if pretrained:
        with open(os.path.join(md5_path, "sim_phase_0"), "rb") as rd:
            data = rd.read()
        with open(os.path.join(data_path, "sim_phase_0"), "wb") as wt:
            wt.write(data)
    else:
        gnn_model = config["gnn_model"]
        gnn_epoch = gnn_config["epoch"]
        seed = config["seed"]
        it_round = config["it_round"]
        top_k=config["top_k"]
        main_main(logger, pretrained, md5, task_path, pair,
                  phase=0, seed=seed, it_round=it_round,topk_corr=top_k, model=gnn_model, gnn_epoch=gnn_epoch)
    logger.info("End [phase 0]")
    # fuse and eval
    # phase 4
    logger.info("Start [phase 4]")
    main_main(logger, pretrained, md5, task_path, pair, phase=4)
    logger.info("End [phase 4]")
