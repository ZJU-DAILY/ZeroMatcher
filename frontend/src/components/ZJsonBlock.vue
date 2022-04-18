<template>
  <div :style="{height:div_height+'px'}">
    <pre style="overflow: auto; height: 100%;"><div
        v-html="syntaxHighlight(JSON.stringify(code, null, 2))"></div></pre>
  </div>
</template>

<script>
export default {
  name: "z-json-block",
  props:{
    _code:Object,
    div_height:Number,
  },
  data(){
    return{
      code: this._code,
    }
  },
  methods:{
    syntaxHighlight(json) {
      if(typeof json ==='undefined'){
        return "";
      }
      if (typeof json != 'string') {
        json = JSON.stringify(json, undefined, 2);
      }
      json = json.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
      return json.replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+-]?\d+)?)/g, function (match) {
        let cls = 'z-number';
        if (/^"/.test(match)) {
          if (/:$/.test(match)) {
            cls = 'z-key';
          } else {
            cls = 'z-string';
          }
        } else if (/true|false/.test(match)) {
          cls = 'z-boolean';
        } else if (/null/.test(match)) {
          cls = 'z-null';
        }
        return '<span class="' + cls + ' z-json">' + match + '</span>';
      });
    },
  },
  watch:{
    _code:function (val){
      this.code=val;
    }
  }
}
</script>

<style scoped>
pre{
  margin: 0;
}
:deep(.z-json) {
  font-size: 1.1rem;
}

:deep(.z-string) {
  color: green;
}

:deep(.z-number) {
  color: #9f5d0c;
}

:deep(.z-boolean) {
  color: blue;
}

:deep(.z-null) {
  color: magenta;
}

:deep(.z-key){
  color: #9B59B6;
}
</style>