<template>
  <div>
    <n-grid :cols="21">
      <n-gi :offset="key==='Entity Resolution Configuration'?0:1" :span="10" v-for="(val,key) in data" :key="key">
        <n-card :title="key" class="z-card">
          <z-json-block :_code="val" :div_height="520"></z-json-block>
        </n-card>
      </n-gi>
    </n-grid>
  </div>
</template>

<script setup>
import {inject, ref} from "vue";
import ZJsonBlock from "./ZJsonBlock.vue";
const config = inject("config")
const gnn_config = inject("gnn_config")
const data=ref({
  "Entity Resolution Configuration":config,
  "GNN Configuration":gnn_config,
})
</script>