<template>
  <div style="padding: 1.5rem;">
    <n-grid :cols="48">
      <n-gi :span="sys_config.jietu?14:6"></n-gi>
      <n-gi :offset="1" :span="sys_config.jietu?18:34">
        <n-card title="Parameter Initialization" class="z-card blue">
          <n-form label-placement="left" :label-width="190">
            <n-form-item label="Input datasets">
              <n-space vertical class="full-width" style="width: 100%;">
                <n-upload :action="sys_config.baseHttp+'/upload'" @finish="handleFinish" v-if="showUploader">
                  <n-upload-dragger>
                    <div>
                      <n-icon size="48" :depth="3">
                        <archive-icon/>
                      </n-icon>
                    </div>
                    <n-text style="font-size: 16px;">Click or Drag to upload</n-text>
                  </n-upload-dragger>
                </n-upload>
                <n-grid v-if="config.data_type!=='unknown'" :cols="25" class="preview">
                  <n-gi :span="12">
                    <n-table @click="tablePreviewModal(0)" :bordered="false" :single-line="false"
                             style="table-layout: fixed;" class="grey-on-hover">
                      <thead>
                      <tr>
                        <th v-for="col in firstThree(a_ori_columns)" :width="column_width" :key="col">
                          <n-ellipsis :style="{'max-width': (column_width)+'px'}">
                            {{ col }}
                          </n-ellipsis>
                        </th>
                        <th>...</th>
                      </tr>
                      </thead>
                      <tbody>
                      <tr v-for="dt in firstThree(a_ori_data)" :key="dt">
                        <td v-for="col in firstThree(a_ori_columns)" :width="column_width" :key="col">
                          <n-ellipsis :style="{'max-width': (column_width)+'px'}">
                            {{ dt[col] }}
                          </n-ellipsis>
                        </td>
                        <td>...</td>
                      </tr>
                      <tr>
                        <td v-for="i in config['data_type']==='table'?[1,2,3,4]:[1,2,3]" :key="i"
                            :width="(column_width)">...
                        </td>
                      </tr>
                      </tbody>
                    </n-table>
                    <!--demo-->
                    <!-- <p v-if="config.data_type==='table'"><b>table_{{ config.pair[0] }}.csv</b></p>
                    <p v-else-if="config.data_type==='graph'"><b>triples_{{ config.pair[0] }}</b></p>
                    <p v-else><b>table_{{ config.pair[0] }}.csv</b></p> -->
                    <p v-if="config.data_type==='table'"><b>{{ config.pair[0] }}</b></p>
                    <p v-else-if="config.data_type==='graph'"><b>SRPRS / {{ config.pair[0] }}</b></p>
                    <p v-else><b>{{ config.pair[0] }}</b></p>
                  </n-gi>
                  <n-gi :offset="1" :span="12">
                    <n-table @click="tablePreviewModal(1)" :bordered="false" :single-line="false"
                             style="table-layout: fixed;" class="table grey-on-hover">
                      <thead>
                      <tr>
                        <th v-for="col in firstThree(b_ori_columns)" :width="column_width" :key="col">
                          <n-ellipsis :style="{'max-width': (column_width)+'px'}">
                            {{ col }}
                          </n-ellipsis>
                        </th>
                        <th>...</th>
                      </tr>
                      </thead>
                      <tbody>
                      <tr v-for="dt in firstThree(b_ori_data)" :key="dt">
                        <td v-for="col in firstThree(b_ori_columns)" :width="column_width" :key="col">
                          <n-ellipsis :style="{'max-width': (column_width)+'px'}">
                            {{ dt[col] }}
                          </n-ellipsis>
                        </td>
                        <td>...</td>
                      </tr>
                      <tr>
                        <td v-for="i in config['data_type']==='table'?[1,2,3,4]:[1,2,3]" :key="i"
                            :width="(column_width)">...
                        </td>
                      </tr>
                      </tbody>
                    </n-table>
                    <!--for demo-->
                    <!-- <p v-if="config.data_type==='table'"><b>table_{{ config.pair[1] }}.csv</b></p>
                    <p v-else-if="config.data_type==='graph'"><b>triples_{{ config.pair[1] }}</b></p>
                    <p v-else><b>triples_{{ config.pair[1] }}</b></p> -->
                    <p v-if="config.data_type==='table'"><b>{{ config.pair[1] }}</b></p>
                    <p v-else-if="config.data_type==='graph'"><b>SRPRS / {{ config.pair[1] }}</b></p>
                    <p v-else><b>{{ config.pair[1] }}</b></p>
                  </n-gi>
                </n-grid>
              </n-space>
            </n-form-item>
            <n-form-item label="Data Type">
              {{ config.data_type==='table'?'Table':(config.data_type==='graph'?'KG':'Unknown') }}
            </n-form-item>
            <n-form-item :label="config.data_type==='table'?'Table-based Learner':'KG-based Learner'">
              <n-radio
                  v-for="item in config.data_type==='table'? ['CEMT'] : ['EASY','LargeEA','RREA','GCNAlign']"
                  :key="item"
                  :checked="config.er_model === item"
                  :value="item"
                  name="er_model"
                  @change="handleRadioChange">{{ item }}
              </n-radio>
            </n-form-item>
            <div v-if="config.er_model==='CEMT' && sys_config.jietu">
              <n-form-item label="Num of Iterations">
                <n-input-number v-if="config.er_model==='CEMT'" v-model:value="config.epoch"/>
                <n-input-number v-else-if="config.er_model==='EASY'" v-model:value="config.iteration"/>
                <n-input-number v-else v-model:value="config.it_round"/>
              </n-form-item>
            </div>
            <div v-else-if="config.er_model==='CEMT'" style="display: flex;">
              <n-form-item label="Num of Iterations" style="flex: 0 0 40%;">
                <n-input-number v-if="config.er_model==='CEMT'" v-model:value="config.epoch"/>
                <n-input-number v-else-if="config.er_model==='EASY'" v-model:value="config.iteration"/>
                <n-input-number v-else v-model:value="config.it_round"/>
              </n-form-item>
              <!-- <n-form-item label="Fine-tune Model">
                <n-radio
                    v-for="item in ['xlnet','bert','roberta']"
                    :key="item"
                    :checked="config.fine_tune_model === item"
                    :value="item"
                    name="fine_tune_model"
                    @change="handleRadioChange">{{ item }}
                </n-radio>
              </n-form-item> -->
            </div>
            <div v-else>
              <n-form-item  label="Num of Iterations">
                <n-input-number v-if="config.er_model==='CEMT'" v-model:value="config.epoch"/>
                <n-input-number v-else-if="config.er_model==='EASY'" v-model:value="config.iteration"/>
                <n-input-number v-else v-model:value="config.it_round"/>
              </n-form-item>
            </div>
            <n-form-item label="Seeds Generator">
              <n-radio
                  v-for="item in ['CSG','Mutual-NN','ALG']"
                  :key="item"
                  :checked="config.asg === item"
                  :value="item"
                  name="asg"
                  @change="handleRadioChange">{{ item }}
              </n-radio>
            </n-form-item>
            <n-form-item label="KG-based Learner" v-if="config.data_type==='table'">
              <n-radio
                  v-for="item in config.data_type==='table'? ['EASY','LargeEA','RREA','GCNAlign'] : ['EASY','LargeEA','RREA','GCNAlign']"
                  :key="item"
                  :checked="config.gnn_model === item"
                  :value="item"
                  name="gnn_model"
                  @change="handleRadioChange">{{ item }}
              </n-radio>
            </n-form-item>
            <n-form-item label="Num of GNN Epochs" style="position: relative;" v-if="config.data_type==='table'">
              <n-input-number v-model:value="gnn_config.epoch"/>
              <n-button type="success" @click="startTask"
                        style="
                          width: 150px!important;
                  margin-top: 0.6rem;
                  height: 2.1rem;
                position: absolute;
                bottom:0;
                right: 0;
                  " :disabled="!clickable">
                Sumbit
              </n-button>
            </n-form-item>
            <n-form-item label="Num of GNN Epochs" v-if="config.data_type==='graph'">
              <n-input-number v-model:value="gnn_config.epoch"/>
            </n-form-item>
            <n-form-item label="" style="position: relative;" v-if="config.data_type==='graph'">
              <n-button type="success" @click="startTask"
                        style="
                          width: 150px!important;
                  margin-top: 0.6rem;
                  height: 2.1rem;
                position: absolute;
                bottom:0;
                right: 0;
                  " :disabled="!clickable">
                Sumbit
              </n-button>
            </n-form-item>
            <!-- <n-form-item label="Random Seed" style="position: relative;">
              <n-input-number v-model:value="config.seed"/>
              <n-button type="success" @click="startTask"
                        style="
                          width: 150px!important;
                  margin-top: 0.6rem;
                  height: 3rem;
                position: absolute;
                bottom:0;
                right: 0;
" :disabled="!clickable">
                Sumbit
              </n-button>
            </n-form-item> -->
          </n-form>
        </n-card>
      </n-gi>
      <n-gi :offset="1" :span="sys_config.jietu?14:6"></n-gi>
    </n-grid>
    </div>

    <n-modal v-model:show="showModal">
      <n-card style="width: 900px;" :title="modal_title" :bordered="false" size="huge" class="detail">
        <n-table :bordered="false" :single-line="false" style="table-layout: fixed;">
          <thead>
          <tr>
            <th v-for="col in modal_columns" :key="col">
              <n-ellipsis
                  :style="{'max-width': ((config['data_type']==='table'||config['data_type']==='table_graph')?Math.round(400/modal_columns.length):220)+'px'}">
                {{ col }}
              </n-ellipsis>
            </th>
          </tr>
          </thead>
          <tbody>
          <tr v-for="dt in modal_current_data" :key="dt">
            <td v-for="col in modal_columns" :key="col" style="padding: 8px;">
              <n-ellipsis
                  :style="{'max-width': ((config['data_type']==='table'||config['data_type']==='table_graph')?Math.round(400/modal_columns.length):220)+'px'}">
                {{ dt[col] }}
              </n-ellipsis>
            </td>
          </tr>
          </tbody>
        </n-table>
        <template #footer>
          <n-divider/>
          <div>
            <n-pagination
                v-model:page="curPage"
                v-model:page-size="perPage"
                :item-count="modal_data.length"
                :page-sizes="[2,5,10]"
                showSizePicker
                @update:page="render_table"
                show-quick-jumper/>
          </div>
        </template>
      </n-card>
    </n-modal>

    <n-modal v-model:show="showFormatErrorModal">
      <n-card style="width: 600px;" title="Error" closable @close="()=>{showFormatErrorModal.value = false}" :bordered="false" size="huge">
        <n-grid :cols="10">
          <n-gi :span="2">
            <n-icon>
              <error-circle12-filled style="color:#d03050;font-size: 40px;"/>
            </n-icon>
          </n-gi>
          <n-gi :span="8">
            <p style="margin-top: 0;">The format of the dataset is incorrect.</p>
            <p style="margin-top: 0;">Please refer to the format below.</p>
            <p style="margin-top: 0;">For <b>table:</b></p>
            <ul>
              <li>table_{lang_src}.csv</li>
              <li>table_{lang_tgt}.csv</li>
              <li>test.csv</li>
            </ul>
            <p style="margin-top: 0;">For <b>graph:</b></p>
            <ul>
              <li>triples_{lang_src}</li>
              <li>triples_{lang_tgt}</li>
              <li>ent_links</li>
            </ul>
            <p style="margin-top: 0;">For <b>table/graph:</b></p>
            <ul>
              <li>table_{lang_src}.csv</li>
              <li>triples_{lang_tgt}</li>
              <li>ent_links</li>
            </ul>
          </n-gi>
        </n-grid>
        <template #footer></template>
      </n-card>
    </n-modal>
  <!--  <div style="height:200px; width:300px;background-color: rgba(0, 0, 0, 0.1); position:relative;">-->
  <!--    <img src="../assets/loupe.png" width="50" style="position:absolute; top: 40%; left:37%;"/>-->
  <!--  </div>-->
</template>
<script>
import {ErrorCircle12Filled} from "@vicons/fluent";
import { ArchiveOutline as ArchiveIcon } from '@vicons/ionicons5'

export default {
  components: {
    ErrorCircle12Filled,
    ArchiveIcon,
  }
}
</script>

<script setup>
import {ref, watch} from "vue";
import {useRouter} from "vue-router";
import {config as sys_config} from "../config";
import {client} from "../http";
import {useMessage} from "naive-ui";
const msg = useMessage();
const router = useRouter();
const showModal = ref(false);
const showFormatErrorModal = ref(false);
const showUploader=ref(true)


const config = ref({
  data_type: "unknown",
  pair: ["", ""],
  gnn_model: "RREA",
  er_model: "EASY",
  clean: false,
  seed: 2021,
  // CollaborER
  lens: [1363, 3226],
  batch_size: 32,
  epoch: 1,
  max_length: 256,
  // fixed
  // seed_model: "stsb-roberta-base",
  fine_tune_model: "bert",
  // EASY
  iteration: 20,
  // LargeEA
  it_round: 1,
  top_k: 1,
  // 
  asg:"CSG",
});
const gnn_config = ref({
  epoch: 75,
});
const handleRadioChange = (e) => {
  console.log(e.target.name, e.target.value)
  config.value[e.target.name] = e.target.value;
}
const column_width=()=>{
  return sys_config.jietu?(config['data_type']==='table'?40:60):(config['data_type']==='table'?60:90)
}
const startTask = async () => {
  let _config = {
    data_type: config.value.data_type,
    er_model: config.value.er_model,
    pair: config.value.pair[0] + "_" + config.value.pair[1],
    gnn_model: config.value.gnn_model,
    clean: config.value.clean,
    seed: config.value.seed,
  };
  if (_config.data_type === "table") {
    let lens = [a_ori_data.value.length, b_ori_data.value.length];
    _config = Object.assign({}, _config, {
      lenA: lens[0],
      lenB: lens[1],
      batch_size: config.value.batch_size.toString(),
      epoch: config.value.epoch,
      max_length: config.value.max_length,
      seed_model: "stsb-roberta-base",
      fine_tune_model: config.value.fine_tune_model,
    })
  } else {
    _config = Object.assign({}, _config, {
      iteration: config.value.iteration,
    })
  }
  let _gnn_config = {
    epoch: gnn_config.value.epoch,
  };
  // patch
  if(_config.er_model==="CEMT"){
    _config.er_model="CollaborEM";
  }
  console.log(_config)
  console.log(_gnn_config)
  const resp = (await client.post(`v2/task/start?task_id=${task_id.value}`, {
    config: _config,
    gnn_config: _gnn_config,
  })).data;
  console.log(resp)
  // TODO
  if (resp.ok) {
    if (resp.ok === 1) {
      // no pretrained model for demo
      msg.warning("The training process takes a long time, please wait patiently.", {
        duration: 6000,
      })
      await router.push({name: "detail", params: {id: task_id.value}});
    }else if (resp.ok === 2) {
      // pretrained model
      msg.success("Pre-trained model already exists.", {
        duration: 6000,
      })
      await router.push({name: "detail", params: {id: task_id.value}});
    }  else if (resp.ok === 3) {
      // for demo
      msg.success("Pre-trained model already exists.", {
        duration: 6000,
      })
      if(_config["data_type"]==="table"){
        await router.push({name: "detail", params: {id: "ta86ble8-359e-4357-a26b-89736560c6ac"}});
      }else if(_config["data_type"]==="graph"){
        await router.push({name: "detail", params: {id: "gr86ape8-e354-2457-766b-62736560abed"}});
      }
    }
  } else {
    msg.error("Internal Error");
  }
};

const a_ori_columns = ref([])
const a_ori_data = ref([])
const b_ori_columns = ref([])
const b_ori_data = ref([])
const modal_columns = ref([])
const modal_data = ref([])
const modal_current_data = ref([])
const modal_title = ref("");
const firstThree = (arr) => {
  if (arr.length > 3) {
    return arr.slice(0, 3);
  } else {
    return arr;
  }
}
const task_id = ref("");
const clickable=ref(false);
const handleFinish = ({file, event}) => {
  showUploader.value=false
  const resp = JSON.parse(event.target.response);
  if (resp["ok"] === 0) {
    showFormatErrorModal.value = true;
    clickable.value=false;
  } else {
    clickable.value=true;
    config.value.data_type = resp["data_type"];
    if (config.value.data_type === "table") {
      config.value.er_model = "CEMT";
      config.value.asg="ALG";
    } else {
      config.value.er_model = "EASY";
      config.value.asg="CSG";
    }
    if (config.value.data_type === "table_graph") {
      msg.warning("The table data will be automatically converted to graph data.", {
        duration: 7000,
      })
    }
    config.value.pair = resp["pair"];
    task_id.value = resp["task_id"];
    a_ori_columns.value = resp["a_columns"]
    b_ori_columns.value = resp["b_columns"]
    a_ori_data.value = resp["a_data"]
    b_ori_data.value = resp["b_data"]
  }
}

const tablePreviewModal = (idx) => {
  showModal.value = true;
  if (idx === 0) {
    modal_columns.value = a_ori_columns.value;
    modal_data.value = a_ori_data.value;
    if (config.value.data_type === "table") {
      modal_title.value = `table_${config.value.pair[0]}.csv`;
    } else {
      modal_title.value = `triples_${config.value.pair[0]}`;
    }
  } else {
    modal_columns.value = b_ori_columns.value;
    modal_data.value = b_ori_data.value;
    if (config.value.data_type === "table") {
      modal_title.value = `table_${config.value.pair[1]}.csv`;
    } else {
      modal_title.value = `triples_${config.value.pair[1]}`;
    }
  }
  curPage.value = 1;
  render_table(curPage.value);
}
const curPage = ref(1);
const perPage = ref(10);
const render_table = (page) => {
  let st = (page - 1) * perPage.value;
  let ed = Math.min((page) * perPage.value, modal_data.value.length);
  modal_current_data.value = [];
  for (let i = st; i < ed; i++) {
    modal_current_data.value.push(modal_data.value[i]);
  }
};
watch(perPage, () => {
  curPage.value = 1;
  render_table(curPage.value)
});

</script>
<style scoped>
:deep(.full-width>div) {
  width: 100%;
}

:deep(#app > div:nth-child(2) > div > div:nth-child(2) > div > div:nth-child(2) > div > div) {
  width: 100%;
}

:deep(.n-card) {
  width: 100%;
}

:deep(.n-upload--dragger-inside) {
  width: 100%;
}

:deep(.n-upload-trigger) {
  width: 100%;
}

:deep(.n-upload-dragger) {
  width: 100%;
}

:deep(.n-card-header) {
  margin-bottom: 1rem;
}

:deep(.n-card__content) {
  padding-bottom: 0;
}

:deep(.blue>.n-card-header) {
  /*background-color: #d9f7be;*/
  background-color: rgb(235, 241, 233);
}

:deep(.blue .n-card-header__main) {
  color: black;
}

:deep(.green>.n-card-header) {
  background-color: #ccff99;
}

:deep(.yellow>.n-card-header) {
  background-color: #d3cbaf;
}

:deep(.preview table) {
  font-size: 10px;
  user-select: none;
  border: dashed 1px #e0e0e6;
}

:deep(.preview th) {
  padding: 4px;
}

:deep(.preview td) {
  padding: 3px;
}

:deep(.preview table:hover) {
  cursor: pointer;
  /*filter: blur(1px);*/
  border: 1px dashed #18a058;
}

.grey-on-hover {
  position: relative;
  cursor: pointer;
}

.grey-on-hover:before {
  content: "";
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-image: url("../assets/loupe.png");
  background-size: 50px;
  background-repeat: no-repeat;
  background-position: center;
  background-color: rgba(0, 0, 0, 0.1);
  transition: opacity .3s;
  opacity: 0;
  z-index: 2;
}

.grey-on-hover:hover:before {
  opacity: 1;
}

:deep(.n-input-number.full-input) {
  width: 100%;
}

:deep(.n-form-item-feedback-wrapper) {
  min-height: 14px;
}

:deep(table) {
  table-layout: fixed;
  width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}



/* 截图 */
:deep(.n-form-item-label){
  font-size:1.1rem;
  font-weight: bold;
}
:deep(.n-input-number){
  width: 6rem;
}
</style>

