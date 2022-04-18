<template>
  <div>
    <n-grid :cols="24" style="margin-top: 2rem;">
      <n-gi :offset="1" :span="22">
        <div class="z-card" style="padding: 1rem;">
          <n-steps :current="currentRef" :status="currentStatus">
            <n-step v-for="(item,idx) in 
            ['Parameter Initialization','Process Tracking','Matching Results Visualization','Matching Results Evaluation']"                    
            :title="item" description="" @click="go(idx+1)" :key="idx"></n-step>
          </n-steps>
        </div>
      </n-gi>
    </n-grid>
    <n-grid v-if="config" :cols="24" style="margin-top: 1rem;">
      <n-gi :offset="1" :span="22">
        <div style="margin-top: 1rem;margin-bottom: 1rem;">
          <div v-show="currentRef===1">
            <z-task-config-tab></z-task-config-tab>
          </div>
          <div v-show="currentRef===2">
            <z-task-runtime-tab @onFinish="runEnd"></z-task-runtime-tab>
          </div>
          <div v-if="data!==null && columns!==null && categories!==null && left_edges!==null && right_edges!==null"
               v-show="currentRef===3">
            <z-result-tab></z-result-tab>
          </div>
          <div v-if="data!==null && columns!==null && categories!==null && left_edges!==null && right_edges!==null"
               v-show="currentRef===4">
            <!-- <z-analysis-tab></z-analysis-tab> -->
            <z-analysis-tab-v2></z-analysis-tab-v2>
          </div>
        </div>
      </n-gi>
    </n-grid>
    <n-grid :cols="24">
      <n-gi :offset="1" :span="22">
        <n-space justify="flex-end">
          <n-space>
            <n-button type="primary" @click="prev">Prev Step</n-button>
          </n-space>
          <n-space>
            <n-button type="primary" @click="next">Next Step</n-button>
          </n-space>
        </n-space>
      </n-gi>
    </n-grid>
  </div>
</template>
<script setup>
import {useRoute} from "vue-router"
import {ref, provide, onMounted} from "vue";
import {useMessage} from "naive-ui"
import ZTaskRuntimeTab from "../components/ZTaskRuntimeTab.vue";
import ZTaskConfigTab from "../components/ZTaskConfigTab.vue";
import ZResultTab from "../components/ZResultTab.vue";
import ZAnalysisTab from "../components/ZAnalysisTab.vue";
import ZAnalysisTabV2 from "../components/ZAnalysisTabV2.vue";
import {client, localClient} from "../http";
import {config as sys_config} from "../config";
import moment from "moment";

const route = useRoute();
const currentRef = ref(2); // 2
const currentStatus = ref('process');
const msg = useMessage();
const end = ref(false);
const runEnd = () => {
  getData().then(() => {
    end.value = true;
    currentRef.value = 3;
    msg.success("Task Finished!")
  });
}
const go = (idx) => {
  if ((idx === 3 || idx === 4) && !end.value) {
    msg.error("Task is not finished yet!")
    return;
  }
  currentRef.value = idx;
}
const prev = () => {
  if (currentRef.value >1) {
    go(currentRef.value - 1);
  }
};
const next = () => {
  if (currentRef.value < 4) {
    go(currentRef.value + 1);
  }
}
const config = ref({})
const gnn_config = ref({})
provide("config", config);
provide("gnn_config", gnn_config);

const getConfig = async () => {
  let task_id = route.params.id;
  const data = (await client.post(`task/config?task_id=${task_id}`)).data;
  config.value = data["config"];
  gnn_config.value = data["gnn_config"];
}
const data = ref(null);
const columns = ref(null);
const categories = ref(null);
const left_edges = ref(null);
const right_edges = ref(null);
const current_result = ref(null);
const historical_result = ref(null);
provide("data", data);
provide("columns", columns);
provide("categories", categories);
provide("left_edges", left_edges);
provide("right_edges", right_edges);
provide("current_result", current_result);
provide("historical_result", historical_result);
// TODO
const getData = async () => {
  let task_id = route.params.id;
  const resp = (await client.post(`task/result?task_id=${task_id}`)).data;
  const meta = resp["meta"]
  current_result.value = []
  let obj = {
    pair: config.value["pair"],
    dataset: config.value["pair"],
    data_type: config.value["data_type"],
    er_model: config.value["er_model"],
    gnn_model: config.value["gnn_model"],
    precision: meta["precision"],
    recall: meta["recall"],
    f1: meta["f1-score"],
    hits_1:meta["hits@1"],
    hits_5:meta["hits@5"],
    mrr:meta["mrr"],
    run_time: (meta["complete_time"] - meta["start_time"]).toFixed(1).toString()+"s",
    end_time: moment.unix(meta["complete_time"]).format("YYYY-MM-DD hh:mm:ss"),
    config: config.value,
    gnn_config: gnn_config.value,
  }
  current_result.value.push(obj);
  data.value = resp["result_data"];
  columns.value = resp["result_columns"];
  categories.value = resp["result_categories"];
  left_edges.value = resp["result_left_edges"];
  right_edges.value = resp["result_right_edges"];
  const resp1 = (await client.get("result")).data;
  historical_result.value = resp1["historical_result"];
}
onMounted(() => {
  getConfig();
  if(sys_config.jietu){
    runEnd();
  }
})
</script>
<script>
export default {
  name: "Detail"
}
</script>

<style scoped>
:deep(.n-step-indicator) {
  cursor: pointer;
}
:deep(.n-step-content) {
  cursor: pointer;
}
</style>