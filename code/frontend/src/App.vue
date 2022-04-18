<template>
  <z-header></z-header>
  <n-dialog-provider>
  <n-message-provider>
    <router-view/>
  </n-message-provider>
  </n-dialog-provider>
  <z-footer></z-footer>
</template>

<script>
import ZHeader from "./components/ZHeader.vue";
import ZFooter from "./components/ZFooter.vue";
export default {
  name: 'App',
  components: {
    ZHeader,
    ZFooter,
  }
}
</script>
