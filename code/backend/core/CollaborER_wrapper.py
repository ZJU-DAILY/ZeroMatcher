from __future__ import annotations
import os
import loguru
from core.entity_resolution.gnn_models.wrapper import ModelWrapper
from core.utils import has_pretrained_model, task_md5_hash
from core.entity_resolution.CollaborER.seeds_wrapper import seeds_main
from core.entity_resolution.CollaborER.table2kg_attr_wrapper import table2kg_main
from core.entity_resolution.CollaborER.train_wrapper import train_main


def CollaborER_have_fun(
        logger: loguru.Logger,
        task_path: str,
        data_path: str,
        config: dict,
        gnn_config: dict,
):
    seed = int(config["seed"])
    epoch = int(config["epoch"])
    gnn_epoch = int(gnn_config["epoch"])
    clean = bool(config["clean"])
    pair = str(config["pair"])
    lang_sr, lang_tg = pair.split("_")
    gnn_model = config["gnn_model"]

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

    md5 = task_md5_hash(task_path)
    pretrained = has_pretrained_model(md5)
    print(f"md5: {md5}")

    # generate seeds
    logger.info("Start [generate seeds]")
    seeds_main(logger, pretrained, md5, task_path, seed)
    logger.info("End [generate seeds]")

    # table2kg
    logger.info("Start [table2kg]")
    table2kg_main(logger, task_path)
    logger.info("End [table2kg]")

    logger.info(f"Start [train {gnn_model}]")
    md5_path = os.path.join(os.getcwd(), "pretrained", md5)

    files = ["test"]
    if os.path.exists(os.path.join(data_path, "train.csv")):
        files.append("train")
    if os.path.exists(os.path.join(data_path, "valid.csv")):
        files.append("valid")

    if pretrained:
        vecA = np.load(os.path.join(md5_path, f"{gnn_model}_embeddingA.npy"))
        vecB = np.load(os.path.join(md5_path, f"{gnn_model}_embeddingB.npy"))
        np.save(os.path.join(data_path, f"{gnn_model}_embeddingA.npy"), vecA)
        np.save(os.path.join(data_path, f"{gnn_model}_embeddingB.npy"), vecB)
    else:
        os.environ["TOKENIZERS_PARALLELISM"] = "true"
        # rel [r..]，一列，edge_index [[u..],[v..]]，两列
        rels = [None] * 2
        rel_sizes = [None] * 2
        edge_index_subs = [None] * 2
        edge_index_objs = [None] * 2
        edge_index = [None] * 2
        # ent_sizes !== lenA,lenB, including entities,values
        ent_sizes = [None] * 2
        for (idx, lang) in enumerate([lang_sr, lang_tg]):
            rels[idx] = []
            edge_index_subs[idx] = []
            edge_index_objs[idx] = []
            mx = 0
            pairs = np.loadtxt(os.path.join(data_path, f"triples_{lang}.txt"), dtype=int, delimiter="\t")
            for sub, obj, rel in pairs:
                rels[idx].append(rel)
                edge_index_subs[idx].append(sub)
                edge_index_objs[idx].append(obj)
                mx = max(mx, int(rel) + 1)
            rel_sizes[idx] = mx
            rels[idx] = torch.Tensor(rels[idx])
            edge_index[idx] = torch.stack(
                [torch.tensor(edge_index_subs[idx]), torch.tensor(edge_index_objs[idx])], dim=0)
            with open(os.path.join(data_path, f"id2entity_{lang}.txt"), 'r') as rd:
                ent_sizes[idx] = len(rd.readlines())
        g1 = []
        g2 = []

        # for file in ["train", "valid", "test"]:
        for file in files:
            with open(os.path.join(data_path, f"{file}.csv"), 'r') as rd:
                for line in rd.readlines()[1:]:
                    a, b, lb = list(map(int, line.split(",")))
                    if lb == 1:
                        g1.append(a)
                        g2.append(b)
        model = ModelWrapper(
            name=gnn_model,
            task_path=task_path,
            lang=pair,
            srprs=False,
            # ei et ent_sizes rel_sizes for construct_adj()
            ei=edge_index,
            et=rels,
            ent_sizes=ent_sizes,
            rel_sizes=rel_sizes,
            link=torch.stack([torch.tensor(g1), torch.tensor(g2)], dim=0),
            device="cuda" if torch.cuda.is_available() else "cpu",
            dim=200,
            epoch=gnn_epoch,
        )
        # entity_seeds.txt for update_trainset()
        train_set1 = []
        train_set2 = []
        with open(os.path.join(data_path, "entity_seeds.txt"), "r") as rd:
            for line in rd.readlines():
                a, b = list(map(int, line.split("\t")))
                train_set1.append(a)
                train_set2.append(b)
        model.update_trainset(np.array([train_set1, train_set2]))
        # train 1 step
        model.train1step(epoch=gnn_epoch)
        # get_curr_embeddings
        vecs = model.get_curr_embeddings()
        # just get entities' embeddings
        if type(vecs[0]) == torch.Tensor:
            vecs = (vecs[0].cpu(), vecs[1].cpu())
        np.save(os.path.join(data_path, f"{gnn_model}_embeddingA.npy"),
                vecs[0][:config["lenA"]])
        np.save(os.path.join(data_path, f"{gnn_model}_embeddingB.npy"),
                vecs[1][:config["lenB"]])
        if not os.path.exists(md5_path):
            os.mkdir(md5_path)
        np.save(os.path.join(md5_path, f"{gnn_model}_embeddingA.npy"),
                vecs[0][:config["lenA"]])
        np.save(os.path.join(md5_path, f"{gnn_model}_embeddingB.npy"),
                vecs[1][:config["lenB"]])
    logger.info(f"End [train {gnn_model}]")

    logger.info("Start [CollaborER train]")
    train_main(logger, pretrained, md5, task_path, seed, epoch, gnn_model, all=len(files) == 3)
    logger.info("End [CollaborER train]")
