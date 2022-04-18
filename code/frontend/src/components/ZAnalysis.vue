<template>
  <n-table>
    <thead>
    <tr>
      <th width="200">Dataset</th>
      <th>Data Type</th>
      <th v-if="current_data && current_data[0]['data_type']=='table'">table-based Learner</th>
      <th v-if="current_data && current_data[0]['data_type']=='table'">KG-based Learner</th>
      <th v-if="current_data && current_data[0]['data_type']=='graph'">KG-based Learner</th>
      <th>Seeds Generator</th>
      <th v-if="current_data && current_data[0]['data_type']=='table'">Precision</th>
      <th v-if="current_data && current_data[0]['data_type']=='table'">Recall</th>
      <th v-if="current_data && current_data[0]['data_type']=='table'">F1-Score</th>
      <th v-if="current_data && current_data[0]['data_type']=='graph'">Hits@1</th>
      <th v-if="current_data && current_data[0]['data_type']=='graph'">Hits@5</th>
      <th v-if="current_data && current_data[0]['data_type']=='graph'">MRR</th>
      <!-- <th>Run Time</th> -->
      <!-- <th>End Time</th> -->
      <!-- <th>Configurations</th> -->
    </tr>
    </thead>
    <tbody>
    <tr v-for="(dt,idx) in current_data" :key="idx">
      <td>{{dt["dataset"]}}</td>
      <td>{{dt["data_type"]==='table'?dt["data_type"]:'KG'}}</td>
      <td>{{dt["er_model"]}}</td>
      <td v-if="current_data && current_data[0]['data_type']=='table'">{{dt["gnn_model"]}}</td>
      <td>{{dt["asg"]}}</td>
      <td v-if="current_data && current_data[0]['data_type']=='table'">{{dt["precision"]?dt["precision"]:'-'}}</td>
      <td v-if="current_data && current_data[0]['data_type']=='table'">{{dt["recall"]?dt["recall"]:'-'}}</td>
      <td v-if="current_data && current_data[0]['data_type']=='table'">{{dt["f1"]?dt["f1"]:'-'}}</td>
      <td v-if="current_data && current_data[0]['data_type']=='graph'">{{dt["hits_1"]?dt["hits_1"]:'-'}}</td>
      <td v-if="current_data && current_data[0]['data_type']=='graph'">{{dt["hits_5"]?dt["hits_5"]:'-'}}</td>
      <td v-if="current_data && current_data[0]['data_type']=='graph'">{{dt["mrr"]?dt["mrr"]:'-'}}</td>
      <!-- <td>{{dt["run_time"]}}</td> -->
      <!-- <td>{{dt["end_time"]}}</td> -->
      <!-- <td><n-button @click="showConfigModal(idx)">Detail</n-button></td> -->
    </tr>
    </tbody>
  </n-table>
  <n-modal v-model:show="showModal">
    <n-card style="width: 900px;" title="Configurations" :bordered="false" size="huge">
      <n-grid :cols="21">
        <n-gi  :span="10">
          <n-card title="ER Config" class="z-card">
            <z-json-block :_code="config" :div_height="480"></z-json-block>
          </n-card>
        </n-gi>
        <n-gi :offset="1" :span="10">
          <n-card title="GNN Config" class="z-card">
            <z-json-block :_code="gnn_config" :div_height="480"></z-json-block>
          </n-card>
        </n-gi>
      </n-grid>
      <template #footer></template>
    </n-card>
  </n-modal>
  <div v-if="pagination" style="margin-top: 1rem;">
    <n-pagination
        v-model:page="curPage"
        v-model:page-size="perPage"
        :item-count="data.length"
        :page-sizes="[2,3,5,10]"
        showSizePicker
        @update:page="render"
        show-quick-jumper/>
  </div>
</template>

<script setup>
import ZJsonBlock from "./ZJsonBlock.vue";
import {onMounted, ref, watch} from "vue";

const curPage = ref(1);
const perPage = ref(3);
const current_data=ref(null);
watch(perPage, () => {
  curPage.value = 1;
  render(curPage.value);
});
onMounted(()=>{
  curPage.value = 1;
  render(curPage.value);
})
const render = (page) => {
  let st = (page - 1) * perPage.value;
  let ed = Math.min((page) * perPage.value, props.data.length);
  current_data.value = [];
  for (let i = st; i < ed; i++) {
    current_data.value.push(props.data[i]);
  }
};
const showModal=ref(false);
const config=ref(null);
const gnn_config=ref(null);
const showConfigModal=(idx)=>{
  config.value=current_data.value[idx].config;
  gnn_config.value=current_data.value[idx].gnn_config;
  showModal.value=true;
}

const props = defineProps({
  data:Array,
  pagination:Boolean,
})
</script>
<script>
export default {
  name: "z-analysis"
}
</script>

<style scoped>
:deep(th){
  background-color: #e1e1e3;
}
/* 截图 */
/* if sys_config.jietu */
/* :deep(td){
  padding: 1px 10px;
  font-size: 1.5rem;
}
:deep(th){
  padding: 1px 10px;
  font-weight: bold;
  font-size: 1.5rem;
} */
/* else */
:deep(th){
  font-weight: bold;
  font-size: 1.0rem;
  padding-top: 4px;
  padding-bottom: 4px;
}
:deep(td) {
  padding-top: 4px;
  padding-bottom: 4px;
  font-size: 1.0rem;
}
</style>