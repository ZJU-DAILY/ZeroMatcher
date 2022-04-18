from __future__ import annotations
import json
import argparse
import os
import random
import numpy as np
import torch
import torch.nn as nn
from datetime import datetime

import loguru
from torch.utils.data import DataLoader
from transformers import AdamW
from apex import amp
import sys

from core.utils import getTaskLogger
from core.entity_resolution.CollaborER.dataloader import TrainDataset, TestDataset
from core.entity_resolution.CollaborER.model import LMNet
from core.entity_resolution.CollaborER.utils import *


def train(model, train_set, optimizer, batch_size, scheduler=None, fp16=True):
    """
    Perform one epoch of the training process.

    Args:
    model: the current model
    train_set: the training dataset
    optimizer: the optimizer for training (e.g., Adam)
    scheduler: the scheduler for training
    batch_size (int, optional): the batch size
    fp16 (boolean): whether to use fp16

    Returns:
        None
    """
    iterator = DataLoader(dataset=train_set,
                          batch_size=batch_size,
                          shuffle=True,
                          num_workers=8,
                          worker_init_fn=worker_init,
                          collate_fn=TrainDataset.pad)
    criterion = nn.CrossEntropyLoss()
    dist_criterion = nn.CosineEmbeddingLoss(margin=0.5)
    model.train()
    for batch in iterator:
        x, y, seqlen, sample, sentencesA, sentencesB = batch
        y = torch.tensor(y).cuda()
        x = torch.tensor(x).view(y.size(0), -1).cuda()
        sentencesA = torch.tensor(sentencesA).view(y.size(0), -1).cuda()
        sentencesB = torch.tensor(sentencesB).view(y.size(0), -1).cuda()
        sample = torch.LongTensor(sample).view(y.size(0), -1)

        # forward
        optimizer.zero_grad()
        logits, _, eA, eB = model(x, sample, sentencesA, sentencesB)

        logits = logits.view(-1, logits.size(-1))
        y = y.view(-1)

        bce_loss = criterion(logits, y)

        y_ = 2 * y
        y_ -= 1
        dist_loss = dist_criterion(eA, eB, y_)

        loss = bce_loss + 0.2 * dist_loss

        # back propagation
        if fp16:
            with amp.scale_loss(loss, optimizer) as scaled_loss:
                scaled_loss.backward()
        else:
            loss.backward()
        optimizer.step()
        if scheduler:
            scheduler.step()


def eval_model(model, dataset, save_result=False, data_path=""):
    iterator = DataLoader(dataset=dataset,
                          batch_size=256,
                          collate_fn=TestDataset.test_pad)
    model.eval()
    y_truth = []
    y_pre = []
    pairs = []
    for batch in iterator:
        x, y, seqlens, sample = batch
        x = torch.tensor(x).squeeze().cuda()
        sample = torch.LongTensor(sample).squeeze()
        with torch.no_grad():
            logits, _ = model(x, sample)
            for item in y:
                y_truth.append(item[0])
            for item in _.cpu().numpy().tolist():
                y_pre.append(item)
        if save_result:
            idx = 0
            for yi in y:
                if yi[0] == 1:
                    pairs.append([int(sample[idx][0].item()), int(sample[idx][1].item())])
                idx += 1
    if save_result:
        pairs = np.array(pairs)
        save_path = os.path.join(data_path, "result.txt")
        np.savetxt(save_path, pairs, fmt="%d", delimiter="\t")
    precision, recall, F1 = evaluate(y_truth, y_pre)
    return precision, recall, F1


def train_main(
        logger: loguru.Logger,
        pretrained: bool,
        md5: str = "",
        task_path: str = "",
        seed: int = 2021,
        n_epoch: int = 5,
        gnn_model="",
        vis_device: str = "0",
        save_model: bool = True,
        scheduler: bool = False,
        fp16: bool = True,
        lr: float = 2e-5,
        skip: bool = True,
        add_token: bool = True,
        all: bool = False,
):
    os.environ['CUDA_VISIBLE_DEVICES'] = "0"

    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    os.environ['PYTHONHASHSEED'] = str(seed)

    data_path = os.path.join(task_path, "dataset")
    config = json.load(open(os.path.join(task_path, 'config.json')))

    md5_path = os.path.join(os.getcwd(), "pretrained", md5)

    max_length = int(config['max_length'])
    batch_size = int(config['batch_size'])
    model_name = config['fine_tune_model']
    pair = config["pair"]
    path = data_path
    # logger = getTaskLogger(task_path)
    logger.info(
        f"task_path: {task_path}, seed: {seed}, n_epoch: {n_epoch}, gnn_model: {gnn_model}, vis_device: {vis_device}")
    logger.info(
        f"save_model: {save_model}, scheduler: {scheduler}, fp16: {fp16}, lr: {lr}, skip: {skip}, add_token: {add_token}")
    logger.info(config)
    logger.info('Seed: {}'.format(torch.initial_seed()))

    train_set = TrainDataset(path, pair, model_name, max_length, skip=skip, add_token=add_token)

    test_set = TestDataset(path, pair, True, model_name, max_length, skip=skip, add_token=add_token)
    all_set = None
    if all:
        all_set = TestDataset(path, pair, False, model_name, max_length, skip=skip, add_token=add_token)

    model = LMNet(
        finetuning=True,
        lm=model_name,
        data_path=path,
        use_rrea_gnn=gnn_model == "RREA",
        use_gcn_align=gnn_model == "gcn_align",
    )
    model = model.cuda()
    print("pretrained: ",pretrained)
    if pretrained:
        model.load_state_dict(torch.load(os.path.join(md5_path, "final_model.pt")))
        test_precision, test_recall, test_F1 = eval_model(model, test_set, True, data_path)
    else:
        optimizer = AdamW(model.parameters(), lr=lr)
        if fp16:
            model, optimizer = amp.initialize(model, optimizer, opt_level='O2')

        test_precision, test_recall, test_F1 = 0.0, 0.0, 0.0

        for epoch in range(1, n_epoch + 1):
            logger.info('epoch: {}'.format(epoch))

            torch.cuda.empty_cache()
            train(model,
                  train_set,
                  optimizer,
                  batch_size,
                  scheduler=None)

            torch.cuda.empty_cache()
            if epoch == n_epoch:
                test_precision, test_recall, test_F1 = eval_model(model, test_set, True, data_path)
            else:
                test_precision, test_recall, test_F1 = eval_model(model, test_set)
            logger.info(
                '[Test]  precision: {:.4f}  recall: {:.4f}  F1: {:.4f}'.format(test_precision, test_recall, test_F1))
            if all:
                all_precision, all_recall, all_F1 = eval_model(model, all_set)
                logger.info(
                    '[All]  precision: {:.4f}  recall: {:.4f}  F1: {:.4f}'.format(all_precision, all_recall, all_F1))

            if save_model:
                torch.save(model.state_dict(), os.path.join(md5_path, "final_model.pt"))

        logger.info('Finish training!')
    logger.info('[Result]')
    logger.info(
        '[Test]  precision: {:.4f}  recall: {:.4f}  F1: {:.4f}'.format(test_precision, test_recall, test_F1))
    if all:
        all_precision, all_recall, all_F1 = eval_model(model, all_set)
        logger.info(
            '[All]  precision: {:.4f}  recall: {:.4f}  F1: {:.4f}'.format(all_precision, all_recall, all_F1))
