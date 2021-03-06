from argparse import ArgumentParser

from data_utils import DBP15K_PAIRS
from dbp15k import DBP15k
from srprs import SRPRS, CPM_TYPES

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--pair', type=str, default='en_fr')
    parser.add_argument('--use_fasttext', default=False, action='store_true')
    parser.add_argument('--use_cpm', default=False, action='store_true')
    parser.add_argument('--device', type=str, default='cuda')

    parser.add_argument("--task_path",type=str)

    args = parser.parse_args()

    pair = args.pair
    task_path=args.task_path
    if pair in DBP15K_PAIRS:
        DBP15k('dataset/DBP15K', pair, task_path=task_path,device=args.device)
    else:
        SRPRS('dataset/SRPRS', pair,
              use_fasttext=args.use_fasttext,
              cpm_types=CPM_TYPES if args.use_cpm else None,
              task_path=task_path,
              device=args.device)
