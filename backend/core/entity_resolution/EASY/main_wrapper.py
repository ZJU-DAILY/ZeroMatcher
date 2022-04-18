from __future__ import annotations
import argparse

import gc
import os

import loguru
import torch

from core.entity_resolution.EASY.eval import *
from core.entity_resolution.EASY.framework import FinalFantasy


def save_memory(dataset):
    dataset.x1 = dataset.x2 = None
    dataset.x2y_mask = dataset.y2x_mask = None
    # dataset.sim_x2y = dataset.sim_y2x = None
    return dataset


def train(logger: loguru.Logger,
          pretrained: bool,
          md5: str, name, task_path, model, nit, epoch, iter_type, refine_it, device, only_gnn, no_neap, no_lev,
          dbp15k=True, _eval: bool = True, ):
    cosine = no_neap
    # use_cache = not args.reload_sim
    lev = not no_lev
    logger.info(f"current dataset: {name}")
    with torch.no_grad():
        file_path = os.path.join(task_path, "dataset", "processed", f"{name}.pt")
        dataset = torch.load(file_path)[0].to(device)
        dataset.ent1_len = dataset.x1.size(0)
        dataset.ent2_len = dataset.x2.size(0)
        if cosine:
            dataset.cosine_x2y = cosine_sim(dataset.x1, dataset.x2)
            dataset.cosine_y2x = dataset.cosine_x2y.t()
        dataset = save_memory(dataset)
        dataset_name = "dbp15k_" + name if dbp15k else "srprs_" + name

        logger.info("-- begin train")
        model_name = model
        model = FinalFantasy(
            logger=logger,
            dataset=dataset,
            task_path=task_path,
            name=dataset_name,
            model=model_name,
            _pair=name,
            srp=not dbp15k,
            fuse_semantic=not cosine,
            fuse_lev_dist=lev,
            _eval=_eval).to(device)
        md5_path = os.path.join(os.getcwd(), "pretrained", md5)
        print(pretrained)
        if pretrained:
            model.load_state_dict(torch.load(os.path.join(md5_path, "final_model.pt")))
            model.load_gnn_emb(md5_path)
            with open(os.path.join(md5_path, "ent_name2id"), "rb") as rd:
                data = rd.read()
            with open(os.path.join(task_path, "dataset", "ent_name2id"), "wb") as wt:
                wt.write(data)
        else:
            model.train_myself(num_it=nit, refine_begin=refine_it, epoch=epoch, iter_type=iter_type, only_gnn=only_gnn)
            torch.save(model.state_dict(), os.path.join(md5_path, "final_model.pt"))
            model.save_gnn_emb(md5_path)
            with open(os.path.join(task_path, "dataset", "ent_name2id"), "rb") as rd:
                data = rd.read()
            with open(os.path.join(md5_path, "ent_name2id"), "wb") as wt:
                wt.write(data)
        # model.train_myself(num_it=nit, refine_begin=refine_it, epoch=epoch, iter_type=iter_type, only_gnn=only_gnn)
        # torch.save(model.state_dict(), os.path.join(md5_path, "final_model.pt"))
        # model.save_gnn_emb(md5_path)
        # with open(os.path.join(task_path, "dataset", "ent_name2id"), "rb") as rd:
        #     data = rd.read()
        # with open(os.path.join(md5_path, "ent_name2id"), "wb") as wt:
        #     wt.write(data)
        if _eval:
            model.eval_myself()
        model.save_align_pair()


def main_main(
        logger: loguru.Logger,
        pretrained: bool,
        md5: str,
        task_path: str,
        seed: int,
        pair: str,
        model: str,
        n_it: int = 20,
        epoch: int = 30,
        no_neap: bool = False,
        no_lev: bool = False,
        iter_type: str = "ours",
        refine_begin: int = 1,
        device: str = "cuda",
        only_gnn: bool = False,
        _eval: bool = True,
):
    set_seed(seed)
    dbp15k = pair in DBP15K_PAIRS
    train(logger, pretrained, md5, pair, task_path, model, n_it, epoch, iter_type, refine_begin, device, only_gnn,
          no_neap, no_lev, dbp15k, _eval)
    gc.collect()