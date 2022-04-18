from __future__ import annotations

import os

import loguru

from core.entity_resolution.EASY.data_utils import DBP15K_PAIRS
from core.entity_resolution.EASY.dbp15k import DBP15k
from core.entity_resolution.EASY.srprs import SRPRS, CPM_TYPES


def neap_main(
        logger: loguru.Logger,
        pretrained: bool,
        md5: str = "",
        task_path: str = "",
        pair: str = "",
        use_fasttext: bool = False,
        use_cpm: bool = False,
        device: str = "cuda",
        _eval:bool=True,
):
    md5_path = os.path.join(os.getcwd(), "pretrained", md5)
    processed_path = os.path.join(task_path, "dataset", "processed")
    processed_file = os.path.join(processed_path, f"{pair}.pt")
    if pretrained:
        with open(os.path.join(md5_path, f"{pair}.pt"), "rb") as rd:
            data = rd.read()
        if not os.path.exists(processed_path):
            os.mkdir(processed_path)
        with open(processed_file, "wb") as wt:
            wt.write(data)
    else:
        if pair in DBP15K_PAIRS:
            DBP15k(pair, task_path=task_path, device=device,_eval=_eval)
        else:
            SRPRS(pair,
                  use_fasttext=use_fasttext,
                  cpm_types=CPM_TYPES if use_cpm else None,
                  task_path=task_path,
                  device=device,_eval=_eval)
        with open(processed_file, "rb") as rd:
            data = rd.read()
        if not os.path.exists(md5_path):
            os.mkdir(md5_path)
        with open(os.path.join(md5_path, f"{pair}.pt"), "wb") as wt:
            wt.write(data)
