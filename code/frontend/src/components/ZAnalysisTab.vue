<template>
  <div>
    <n-card class="z-card" title="Current Result">
      <z-analysis v-if="current_result" :data="current_result"></z-analysis>
    </n-card>
    <n-card class="z-card" style="margin-top: 1rem;" title="Historical Results">
      <z-analysis v-if="historical_result" :data="historical_result" :pagination="true"></z-analysis>
    </n-card>
  </div>
</template>

<script setup>
import ZAnalysis from "./ZAnalysis.vue";
import {inject, ref} from "vue";

const historical_result = inject("historical_result");
const current_result = inject("current_result");
console.log(current_result)
console.log(historical_result)
</script>

<style scoped>
</style>