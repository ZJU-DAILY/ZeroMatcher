import os
import torch
import torch.nn as nn
import numpy as np
from transformers import BertModel, AlbertModel, DistilBertModel, RobertaModel, XLNetModel
model_ckpts = {'bert': os.path.join(os.getcwd(), "core/lm_models/bert-base-uncased"),
               'albert': os.path.join(os.getcwd(), "core/lm_models/albert-base-v2"),
               'roberta': os.path.join(os.getcwd(), "core/lm_models/roberta-base"),
               'xlnet': os.path.join(os.getcwd(), "core/lm_models/xlnet-base-cased"),
               'distilbert': os.path.join(os.getcwd(), "core/lm_models/distilbert-base-uncased")}


class LMNet(nn.Module):
    def __init__(self,
                 finetuning=True,
                 lm='bert',
                 data_path=None,
                 use_rrea_gnn=True,
                 use_gcn_align=True,
                 bert_path=None):
        super().__init__()

        self.path = data_path

        self.use_rrea_gnn = use_rrea_gnn
        self.use_gcn_align = use_gcn_align

        self.RREA_embeddingA = None
        self.RREA_embeddingB = None
        self.gcn_align_embeddingA = None
        self.gcn_align_embeddingB = None

        self.load_gnn_embedding()

        # load the model or model checkpoint
        if bert_path is None:
            if lm == 'bert':
                self.bert = BertModel.from_pretrained(model_ckpts[lm])
            elif lm == 'distilbert':
                self.bert = DistilBertModel.from_pretrained(model_ckpts[lm])
            elif lm == 'albert':
                self.bert = AlbertModel.from_pretrained(model_ckpts[lm])
            elif lm == 'xlnet':
                self.bert = XLNetModel.from_pretrained(model_ckpts[lm])
            elif lm == 'roberta':
                self.bert = RobertaModel.from_pretrained(model_ckpts[lm])

        else:
            output_model_file = bert_path
            model_state_dict = torch.load(output_model_file,
                                          map_location=lambda storage, loc: storage)
            if lm == 'bert':
                self.bert = BertModel.from_pretrained(model_ckpts[lm],
                                                      state_dict=model_state_dict)
            elif lm == 'distilbert':
                self.bert = DistilBertModel.from_pretrained(model_ckpts[lm],
                                                            state_dict=model_state_dict)
            elif lm == 'albert':
                self.bert = AlbertModel.from_pretrained(model_ckpts[lm],
                                                        state_dict=model_state_dict)
            elif lm == 'xlnet':
                self.bert = XLNetModel.from_pretrained(model_ckpts[lm],
                                                       state_dict=model_state_dict)
            elif lm == 'roberta':
                self.bert = RobertaModel.from_pretrained(model_ckpts[lm],
                                                         state_dict=model_state_dict)

        self.finetuning = finetuning
        self.module_dict = nn.ModuleDict({})

        hidden_size = 768
        hidden_dropout_prob = 0.1

        vocab_size = 2

        self.module_dict['classification_dropout'] = nn.Dropout(hidden_dropout_prob)

        if self.use_rrea_gnn:
            self.module_dict['classification_fc1'] = nn.Linear(hidden_size + 600 * 2, vocab_size)
        elif self.use_gcn_align:
            self.module_dict['classification_fc1'] = nn.Linear(hidden_size + 200 * 2, vocab_size)
        else:
            self.module_dict['classification_fc1'] = nn.Linear(hidden_size, vocab_size)

    def load_gnn_embedding(self):
        if self.use_rrea_gnn:
            pathA = os.path.join(self.path, 'RREA_embeddingA.npy')
            pathB = os.path.join(self.path, 'RREA_embeddingB.npy')
            self.RREA_embeddingA = torch.tensor(np.load(pathA), requires_grad=False)
            self.RREA_embeddingB = torch.tensor(np.load(pathB), requires_grad=False)

        if self.use_gcn_align:
            pathA = os.path.join(self.path, 'gcn_align_embeddingA.npy')
            pathB = os.path.join(self.path, 'gcn_align_embeddingB.npy')
            self.gcn_align_embeddingA = torch.tensor(np.load(pathA), requires_grad=False)
            self.gcn_align_embeddingB = torch.tensor(np.load(pathB), requires_grad=False)

    def encode(self, x, batch_size=256):
        dropout = self.module_dict['classification_dropout']
        self.bert.eval()
        embedding = torch.zeros(x.size(0), 768)
        left = 0
        while left < x.size(0):
            right = min(left + batch_size, x.size(0))
            output = self.bert(x[left: right].cuda())
            pooler_output, _ = torch.max(output[0], dim=1)
            embedding[left: right] = dropout(pooler_output)
            left += batch_size
        return embedding

    def forward(self, x, sample, sentencesA=None, sentencesB=None):
        """Forward function of the models for classification."""

        dropout = self.module_dict['classification_dropout']
        fc1 = self.module_dict['classification_fc1']

        # Sentence features
        if self.training and self.finetuning:
            self.bert.train()
            output = self.bert(x)
            cls = output[0][:, 0, :]
            pairs = dropout(cls)
            output = self.bert(sentencesA)
            cls = output[0][:, 0, :]
            pairA = dropout(cls)
            output = self.bert(sentencesB)
            cls = output[0][:, 0, :]
            pairB = dropout(cls)

            pooled_output = pairs
        else:
            self.bert.eval()
            with torch.no_grad():
                output = self.bert(x)
                cls = output[0][:, 0, :]
                pairs = dropout(cls)

                pooled_output = pairs

        # Graph features
        if self.use_rrea_gnn:
            embeddingA = torch.zeros(sample.size(0), 600, requires_grad=False).cuda().half()
            embeddingB = torch.zeros(sample.size(0), 600, requires_grad=False).cuda().half()
            RREA_embeddingA = torch.index_select(self.RREA_embeddingA, 0, sample[:, 0]).cuda().half()
            RREA_embeddingB = torch.index_select(self.RREA_embeddingB, 0, sample[:, 1]).cuda().half()
            embeddingA += RREA_embeddingA
            embeddingB += RREA_embeddingB
        elif self.use_gcn_align:
            embeddingA = torch.zeros(sample.size(0), 200, requires_grad=False).cuda().half()
            embeddingB = torch.zeros(sample.size(0), 200, requires_grad=False).cuda().half()
            gcn_align_embeddingA = torch.index_select(self.gcn_align_embeddingA, 0, sample[:, 0]).cuda().half()
            gcn_align_embeddingB = torch.index_select(self.gcn_align_embeddingB, 0, sample[:, 1]).cuda().half()
            embeddingA += gcn_align_embeddingA
            embeddingB += gcn_align_embeddingB
        else:
            embeddingA = torch.zeros(sample.size(0), 600, requires_grad=False).cuda().half()
            embeddingB = torch.zeros(sample.size(0), 600, requires_grad=False).cuda().half()

        if self.use_rrea_gnn or self.use_gcn_align:
            abs_embedding = torch.abs(embeddingA - embeddingB)
            dot_embedding = embeddingA * embeddingB

            pooled_output = torch.cat((pooled_output, abs_embedding, dot_embedding), dim=1)
        logits = fc1(pooled_output)

        y_hat = logits.argmax(-1)

        if self.training and self.finetuning:
            return logits, y_hat, pairA, pairB
        else:
            return logits, y_hat
