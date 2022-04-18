<template>
  <div style="border-bottom: solid 1px #ededef">
    <n-space justify="space-between" id="z-header">
      <n-menu :options="titleOptions" v-model:value="activeKey" mode="horizontal"></n-menu>
      <n-menu :options="githubOptions" v-model:value="activeKey" mode="horizontal"></n-menu>
    </n-space>
  </div>
</template>
<script setup>
import {h, ref, watch} from 'vue';
import {NIcon} from 'naive-ui';
import {LogoGithub} from '@vicons/ionicons5';
import {CloudDataOps} from "@vicons/carbon";
import {config} from "../config";
import {RouterLink, useRoute} from "vue-router";

const route = useRoute();

function renderIcon(icon) {
  return () => h(NIcon, null, {default: () => h(icon)})
}

const titleOptions = [
  {
    label: () =>
        h(
            RouterLink,
            {
              to: {name: "home"}
            },
            {
              default: () => config.title,
            }
        ),
    key: "title",
    icon: renderIcon(CloudDataOps),
  }
]
const githubOptions = [
  {
    label: () =>
        h(
            'a',
            {
              href: 'https://github.com/ZJU-DAILY/',
              target: '_blank',
            },
            {
              default: () => 'ZJU-DAILY',
            }
        ),
    key: 'lab',
    // 软著
    // icon: renderIcon(LogoGithub)
  },
];
const activeKey = ref(null);
watch(() => route.path, (val, oval) => {
  activeKey.value = null;
  // if (val.startsWith("/detail")) {
  //   activeKey.value = null;
  // }
})
</script>
<script>
export default {
  name: "z-header"
}
</script>
<style scoped>
:deep(.router-link-active) {
}
</style>