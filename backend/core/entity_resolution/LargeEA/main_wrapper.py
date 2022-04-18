from __future__ import annotations

import copy

import loguru

import core.entity_resolution.LargeEA.text_sim as text
from core.entity_resolution.LargeEA.dataset import *
import torch
from core.entity_resolution.LargeEA.eval import sparse_acc, evaluate_embeds, sparse_top_k
from tqdm import tqdm
import logging, random, time
from core.entity_resolution.LargeEA.sampler import *
from core.entity_resolution.LargeEA.fuse import *
import time


def train(batch: AlignmentBatch, it_round: int, epoch: int, ):
    if hasattr(batch, 'skip'):
        return None
    else:
        model = batch.model
        for it in range(it_round):
            model.train1step(epoch)
            if it < it_round - 1:
                model.mraea_iteration()
        return model.get_curr_embeddings('cpu')


def run_batched_ea(data: EAData, logger: loguru.Logger, src_split, trg_split,
                   seed: int = 2020, cuda: bool = True, topk: int = 1,
                   random_split: bool = False, it_round: int = 1, model: str = "RREA", gnn_epoch: int = 100):
    logger.info('read data complete')
    torch.backends.cudnn.deterministic = True
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if cuda and torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
    set_seed(seed)
    device = torch.device("cuda" if cuda and torch.cuda.is_available() else "cpu")
    curr_sim = None
    for batch in tqdm(batch_sampler(data, logger, src_split, trg_split, topk, random=random_split, backbone=model)):
        # Load Data
        embed = train(batch, it_round=it_round, epoch=gnn_epoch)
        logger.info('train_on_batch')
        if embed is None:
            logger.info('batch skipped')
            continue
        sim = batch.get_sim_mat(embed, data.size())
        update_time_logs('get_sim_mat_on_batch')
        res = sparse_acc(sim, batch.test_set, device='cpu')
        logger.info(f'acc={res}')
        logger.info('eval_on_batch')
        curr_sim = sim if curr_sim is None else curr_sim + sim
        logger.info('fuse_sim')

    return curr_sim


def get_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("--cuda", action="store_true", default=True, help="whether to use cuda or not")
    parser.add_argument("--seed", type=int, default=2020, help="random seed")

    # My arguments
    parser.add_argument('--dataset', type=str, default='small')
    parser.add_argument('--lang', type=str, default='fr')
    parser.add_argument('--phase', type=int, default=4)
    parser.add_argument('--src_split', type=int, default=-1)
    parser.add_argument('--trg_split', type=int, default=-1)
    parser.add_argument('--topk_corr', type=int, default=1)
    parser.add_argument('--it_round', type=int, default=1)
    parser.add_argument("--epoch", type=int, default=-1, help="number of epochs to train")
    parser.add_argument('--model', type=str, default='rrea')
    parser.add_argument('--save_prefix', type=str, default='')
    parser.add_argument('--openea', action='store_true', default=False)
    parser.add_argument('--unsup', action='store_true', default=False)
    parser.add_argument('--eval_which', type=str, default='sgtnf')
    parser.add_argument("--random_split", action="store_true", default=False, help="whether to use random split")
    parser.add_argument("--save_folder", type=str, default='tmp4')
    return parser.parse_args()


def load_sims_phase(phases, data_path):
    sims = []
    for p in phases:
        p_path = os.path.join(data_path, f"sim_phase_{p}")
        sims.append(torch.load(p_path))
    return tuple(sims)


def get_semi_link(phases, data_path: str, param=[1., 0.05]):
    x2y_fused = naive_sim_fuser(load_sims_phase(phases, data_path), param, device='cpu')
    y2x_fused = x2y_fused
    x2y_fused = matrix_argmax(x2y_fused, 1)
    y2x_fused = matrix_argmax(y2x_fused, 0)
    mask = get_bi_mapping(x2y_fused, y2x_fused, [x2y_fused.numel(), y2x_fused.numel()])
    return torch.stack(
        [torch.arange(x2y_fused.numel()),
         x2y_fused]
    ).t()[mask].numpy()


def main_main(
        logger: loguru.Logger,
        pretrained: bool,
        md5: str,
        task_path: str,
        pair: str,
        seed: int = 2020,
        gnn_epoch: int = 100,
        phase: int = 4,
        src_split: int = -1,
        trg_split: int = -1,
        topk_corr: int = 1,
        it_round: int = 1,
        model: str = "RREA",
        unsup: bool = False,
        random_split: bool = False,
        eval_which: str = "sgtnf",
):
    lang_sr, lang_tg = str(pair).split("_")
    data_path = os.path.join(task_path, "dataset")
    fsize1 = round(os.path.getsize(os.path.join(data_path, f"triples_{lang_sr}")) / float(1024 * 1024), 0)
    fsize2 = round(os.path.getsize(os.path.join(data_path, f"triples_{lang_tg}")) / float(1024 * 1024), 0)
    if fsize1 > 200 or fsize2 > 200:
        dataset = "large"
    elif fsize1 > 20 or fsize2 > 20:
        dataset = "medium"
    else:
        dataset = "small"
    if src_split < 0:
        src_split = trg_split = dict(small=5, medium=10, large=20)[dataset]
    md5_path = os.path.join(os.getcwd(), "pretrained", md5)
    try:
        d = EAData.load(os.path.join(data_path, f"dataset_{dataset}_{pair}"))
    except:
        if dataset == 'large':
            d = LargeScaleEAData(data_path, pair, False, unsup=unsup)
        else:
            d = OpenEAData(data_path, pair, unsup=unsup)
        d.save(os.path.join(data_path, f"dataset_{dataset}_{pair}"))

    logger.info(f"load_data")
    logger.info(f"dataset: {dataset}")
    logger.info(f"phase: {phase}")
    logger.info(f"random_split: {random_split}")

    if not os.path.exists(md5_path):
        os.mkdir(md5_path)
    if phase == 0:
        semi = get_semi_link([2, 3], data_path, [1., 0.05])
        total_semi = len(semi)
        d.train = semi
        logger.info("get_semi_link")
        logger.info(f"total semi pairs: {total_semi}")
        stru_sim = run_batched_ea(d, logger, src_split, trg_split,
                                  random_split=random_split,
                                  seed=seed,
                                  it_round=it_round,
                                  topk=topk_corr,
                                  model=model,
                                  gnn_epoch=gnn_epoch)
        torch.save(stru_sim, os.path.join(data_path, f"sim_phase_{phase}"))
        torch.save(stru_sim, os.path.join(md5_path, f"sim_phase_{phase}"))
        logger.info("save_curr_sim")
        result = sparse_acc(stru_sim, d.ill(d.test, 'cpu'))
        logger.info(f"acc is: {str(result)}")
    elif phase == 1:
        candidates = SelectedCandidates(d.test, *d.ents)
        logger.info("build_candidates")
        torch.save((candidates, text.get_bert_maxpooling_embs(*candidates.ents)),
                   os.path.join(data_path, "bert_result"))
        torch.save((candidates, text.get_bert_maxpooling_embs(*candidates.ents)),
                   os.path.join(md5_path, "bert_result"))
        logger.info("bert_embedding_of_names")
    elif phase in range(2, 4):
        # for is_train, candidates in enumerate(all_candidates):
        if phase == 2:
            candidates, bert_result = torch.load(os.path.join(data_path, "bert_result"))
            sim = text.global_level_semantic_sim(bert_result)
            logger.info("faiss_topk_search")
        else:
            candidates = SelectedCandidates(d.test, *d.ents)
            logger.info("build_candidates")
            sim = text.sparse_string_sim(*candidates.ents)
            logger.info("build_sparse_string_sim")
        sim = candidates.convert_sim_mat(sim)
        logger.info("convert_sim")
        torch.save(sim, os.path.join(data_path, f"sim_phase_{phase}"))
        torch.save(sim, os.path.join(md5_path, f"sim_phase_{phase}"))
        logger.info("save_sim")
        del candidates
        result = sparse_acc(sim, d.ill(d.test))
        logger.info("get_hits_mrr")
        logger.info(f"result: {str(result)}")
    elif phase == 4:
        global_sim, string_sim, stru_sim = load_sims_phase([2, 3, 0], data_path)
        logger.info("load_sims")
        if stru_sim is not None:
            candidates = SelectedCandidates(d.test, *d.ents)
            stru_sim = candidates.filter_sim_mat(stru_sim)
        logger.info("filter_sim_mat")
        global_sim = global_sim
        string_sim = string_sim * 0.05
        stru_sim = stru_sim
        sims = [global_sim, string_sim]
        fused_name = naive_sim_fuser(sims)
        logger.info("fuse_name_sims")
        fused_all = naive_sim_fuser([stru_sim, fused_name], device='cpu')
        sims = dict(stru_sim_sel=stru_sim, global_sim_sel=global_sim,
                    text_sim_sel=string_sim, name_sim_sel=fused_name,
                    fused_all_sel=fused_all)
        for key, sim in sims.items():
            if sim is not None and key[0] in eval_which:
                # ZXC 这里用cuda跑会有问题
                result = sparse_top_k(sim, d.ill(d.test, 'cpu'), device="cpu")
                logger.info(f'get_hits_mrr_of_{key}')
                logger.info(f"result: {str(result)}")
        # 要排除掉所有sim都为0的
        idx=torch.argmax(fused_all.to_dense(),dim=1)
        pairs = []
        for i,x in enumerate(idx):
            if x!=0:
                pairs.append([i, int(x.item())])
        pairs = np.array(pairs)
        save_path = os.path.join(data_path, "result.txt")
        np.savetxt(save_path, pairs, fmt="%d", delimiter="\t")

