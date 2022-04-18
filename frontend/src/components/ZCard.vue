<template>
<div class="z-card">
  <h2>{{title}}</h2>
  <div></div>
</div>
</template>

<script setup>
const props=defineProps({
  title:String,
})
</script>
<script>
export default {
  name: "ZCard"
}
</script>

<style scoped>

</style>