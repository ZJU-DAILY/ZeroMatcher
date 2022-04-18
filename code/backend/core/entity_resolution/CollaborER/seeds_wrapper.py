from __future__ import annotations

import csv
import json
import os
import random
import time
import loguru

import numpy as np
import torch.cuda
from sentence_transformers import SentenceTransformer, util
from core.entity_resolution.CollaborER.utils import *
from core.utils import getTaskLogger, has_pretrained_model


def sample(topkA, topkB, sim_score, hard_sample=True, left=2, right=10, threshold=0.03):
    pos = set()
    lenA = topkA.shape[0]
    for e1 in range(lenA):
        e2 = topkA[e1][0].item()
        if e1 == topkB[e2][0].item():
            e2_ = topkA[e1][1]
            e1_ = topkB[e2][1]
            score1 = (sim_score[e1][e2] - sim_score[e1][e2_]).item()
            score2 = (sim_score[e1][e2] - sim_score[e1_][e2]).item()

            if score1 >= threshold and score2 >= threshold:
                pos.add((e1, e2, 1))

    neg = negative_sample(pos, topkA, topkB, hard_sample, left, right)
    return pos, neg


def negative_sample(pos, topkA, topkB, hard_sample=True, left=2, right=10):
    neg = set()
    lenA = topkA.shape[0]
    lenB = topkB.shape[0]
    for seed in pos:
        e1, e2, label = seed
        if hard_sample:
            # (2, 10)
            for i in range(left, right):
                if (e1, topkA[e1][i].item(), 1) not in pos:
                    neg.add((e1, topkA[e1][i].item(), 0))
                if (topkB[e2][i].item(), e2, 1) not in pos:
                    neg.add((topkB[e2][i].item(), e2, 0))
        else:
            for i in range(8):
                e = np.random.randint(lenB)
                while e == e2 or (e1, e, 1) in pos:
                    e = np.random.randint(lenB)
                neg.add((e1, e, 0))
                e = np.random.randint(lenA)
                while e == e1 or (e, e2, 1) in pos:
                    e = np.random.randint(lenA)
                neg.add((e, e2, 0))
    return neg


def seeds_main(
        logger: loguru.Logger,
        pretrained: bool,
        md5: str = "",
        task_path: str = "",
        seed: int = 2021,
        hard_sample: bool = True,
        left: int = 2,
        right: int = 10,
        vis_device: str = "0",
):
    os.environ['CUDA_VISIBLE_DEVICES'] = vis_device

    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    os.environ['PYTHONHASHSEED'] = str(seed)

    data_path = os.path.join(task_path, "dataset")
    if not os.path.exists(os.path.join(data_path, 'log')):
        os.mkdir(os.path.join(data_path, 'log'))

    if not os.path.exists(os.path.join(data_path, 'checkpoint')):
        os.mkdir(os.path.join(data_path, 'checkpoint'))

    config = json.load(open(os.path.join(task_path, 'config.json')))
    model_name = config['seed_model']
    model = SentenceTransformer(
        os.path.join(os.getcwd(), "core", "lm_models", model_name))

    pair = config["pair"]
    lang_sr, lang_tg = str(pair).split("_")

    # logger = getTaskLogger(task_path)

    logger.info(f"seed: {seed}, hard_sample: {hard_sample}, left: {left}, right: {right}.")
    if hard_sample:
        logger.info('Hard sample.')

    logger.info('Seed: {}'.format(torch.initial_seed()))
    logger.info('Left: {}, Right: {}'.format(left, right))

    path = data_path
    vecA = os.path.join(path, 'vecA.npy')
    vecB = os.path.join(path, 'vecB.npy')
    md5_path = os.path.join(os.getcwd(), "pretrained", md5)

    logger.info('Compute embedding...')
    if pretrained:
        seeds_path = os.path.join(path, 'seeds.csv')
        with open(os.path.join(md5_path, "seeds.csv"), "r") as rd:
            data = rd.read()
        with open(seeds_path, "w") as wt:
            wt.write(data)
        cnt = 0
        pos_cnt = 0
        neg_cnt = 0
        with open(seeds_path, "r") as rd:
            f_csv = csv.reader(rd)
            headers = next(f_csv)
            for row in f_csv:
                cnt += 1
                if int(row[2]) == 1:
                    pos_cnt += 1
                else:
                    neg_cnt += 1
        logger.info('Num positive seeds: {}.'.format(pos_cnt))
        logger.info('Num negative seeds: {}.'.format(neg_cnt))
        logger.info('Num seeds: {}'.format(cnt))

    else:
        tableA = os.path.join(path, f'table_{lang_sr}.csv')
        tableB = os.path.join(path, f'table_{lang_tg}.csv')
        entityA = read_entity(tableA, skip=True, add_token=True)
        entityB = read_entity(tableB, skip=True, add_token=True)

        # Encode
        embeddingA = model.encode(entityA, batch_size=512)
        embeddingB = model.encode(entityB, batch_size=512)

        # Norm
        embeddingA = [v / np.linalg.norm(v) for v in embeddingA]
        embeddingB = [v / np.linalg.norm(v) for v in embeddingB]

        np.save(vecA, embeddingA)
        np.save(vecB, embeddingB)
        t1 = time.time()

        embeddingA = torch.tensor(embeddingA).cuda()
        embeddingB = torch.tensor(embeddingB).cuda()
        sim_score = util.pytorch_cos_sim(embeddingA, embeddingB)
        distA, topkA = torch.topk(sim_score, k=30, dim=1)
        distB, topkB = torch.topk(sim_score, k=30, dim=0)
        topkB = topkB.t()

        logger.info('Time: {:.4f}.'.format(time.time() - t1))

        pos_seeds, neg_seeds = sample(topkA, topkB, sim_score, hard_sample, left, right)

        logger.info('Num positive seeds: {}.'.format(len(pos_seeds)))
        logger.info('Num negative seeds: {}.'.format(len(neg_seeds)))

        seeds = pos_seeds | neg_seeds
        seeds = list(seeds)

        logger.info('Num seeds: {}'.format(len(seeds)))

        seeds_path = os.path.join(path, 'seeds.csv')
        seeds_writer = csv.writer(open(seeds_path, 'w'))
        seeds_writer.writerow(['ltable_id', 'rtable_id', 'label'])
        seeds_writer.writerows(seeds)
        seeds_path = os.path.join(path, 'seeds.csv')
        with open(seeds_path, "r") as rd:
            data = rd.read()
        if not os.path.exists(md5_path):
            os.mkdir(md5_path)
        with open(os.path.join(md5_path, "seeds.csv"), "w") as wt:
            wt.write(data)
