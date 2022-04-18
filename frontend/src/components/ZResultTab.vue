<template>
  <n-grid :cols="25">
    <n-gi :span="12">
      <n-card class="z-card">
        <div style="height: 567px">
          <n-grid :cols="25">
            <n-gi :span="12">
              <n-table :single-line="false">
                <thead>
                <tr>
                  <th :colspan="A_columns.length" class="z-table-pair" style="background-color: #E74C3C;">{{config['data_type']==='graph'?'SRPRS / ':''}}{{ pair_a }}</th>
                </tr>
                <tr>
                  <th v-for="col in A_columns" style="font-weight: bold;">{{ col.label }}</th>
                </tr>
                </thead>
                <tbody>
                <tr v-for="(row,idx) in A_current_data">
                  <td v-for="(value,key) in row">
                    <n-ellipsis :style="{'max-width': (config['data_type']==='table'?Math.round(220/A_columns.length):240)+'px'}">
                      {{ value }}
                    </n-ellipsis>
                  </td>
                </tr>
                </tbody>
              </n-table>
            </n-gi>
            <n-gi :offset="1" :span="12">
              <n-table :single-line="false">
                <thead>
                <tr>
                  <th :colspan="B_columns.length" class="z-table-pair" style="background-color: #3498DB;">{{config['data_type']==='graph'?'SRPRS / ':''}}{{ pair_b }}</th>
                </tr>
                <tr>
                  <th v-for="col in B_columns" style="font-weight: bold;">{{ col.label }}</th>
                </tr>
                </thead>
                <tbody>
                <tr v-for="(row,idx) in B_current_data">
                  <td v-for="(value,key) in row" :key="key">
                    <n-ellipsis :style="{'max-width': (config['data_type']==='table'?Math.round(220/B_columns.length):240)+'px'}">
                      {{ value }}
                    </n-ellipsis>
                  </td>
                </tr>
                </tbody>
              </n-table>
            </n-gi>
          </n-grid>
          <div style="margin-top: 1rem;">
            <n-pagination
                v-model:page="curPage"
                v-model:page-size="perPage"
                :item-count="data.length"
                :page-sizes="[3,5,10]"
                showSizePicker
                @update:page="render"
                show-quick-jumper/>
          </div>
        </div>
      </n-card>
    </n-gi>
    <n-gi :offset="1" :span="12">
      <n-card class="z-card">
        <div id="graph" style="height: 567px;">
          <div id="er_graph" style="height:520px;width: 608px;"></div>
        </div>
      </n-card>
    </n-gi>
  </n-grid>
</template>

<script setup>
import {computed, inject, onMounted, ref, watch} from "vue";
import {client} from "../http";
import {config as sys_config} from "../config";

const config = inject("config");
console.log('ij',config.value.pair,config.value.dataset)
let pair_a,pair_b;
if(config.value.pair){
  pair_a = ref(config.value.pair.split("_")[0]);
  pair_b = ref(config.value.pair.split("_")[1]);
}else{
  pair_a = ref(config.value.dataset.split("_")[0]);
  pair_b = ref(config.value.dataset.split("_")[1]);
}
const data = inject("data");
const columns = inject("columns");
const A_columns = columns.value.filter((item) => item.field[0] === 'A' && item.label!=='id');
const B_columns = columns.value.filter((item) => item.field[0] === 'B' && item.label!=='id');
const A_data = data.value.map((item) => {
  let dt = {};
  for (const key of Object.keys(item)) {
    if (key[0] === 'A' && key.indexOf("id")===-1) {
      dt[key] = item[key];
    }
  }
  return dt;
});
const B_data = data.value.map((item) => {
  let dt = {};
  for (const key of Object.keys(item)) {
    if (key[0] === 'B' && key.indexOf("id")===-1) {
      dt[key] = item[key];
    }
  }
  return dt;
});
const current_data = ref([]);
const A_current_data = ref([]);
const B_current_data = ref([]);
const curPage = ref(1);
const perPage = ref(10);
watch(perPage, () => {
  curPage.value = 1;
  render(curPage.value)
});
const render = (page) => {
  render_table(page);
  render_graph(page);
};
const render_table = (page) => {
  let st = (page - 1) * perPage.value;
  let ed = Math.min((page) * perPage.value, data.value.length);
  current_data.value = [];
  A_current_data.value = [];
  B_current_data.value = [];
  for (let i = st; i < ed; i++) {
    current_data.value.push(data.value[i]);
    A_current_data.value.push(A_data[i]);
    B_current_data.value.push(B_data[i]);
  }
};
import * as echarts from "echarts";

const graph = ref(null);
const graph_option = ref(null);
const myRed = "#E74C3C";
const myBlue = "#3498DB";
const myPurple = "#8E44AD";
const categories = inject("categories");
const left_edges = inject("left_edges");
const right_edges = inject("right_edges");
// 两个实体节点y轴间隔
const y_gap = {"2": 1000,"3": 500, "5": 200, "10": 100}
// x轴
const x_gap = {"2": 1000, "3": 500,"5": 300, "10": 300}
const render_graph = (page) => {
  if (graph.value != null
      && typeof graph.value !== "undefined"
      && Object.keys(graph.value).length !== 0) {
    graph.value.clear();
    graph.value.dispose();
  }
  graph.value = echarts.init(document.getElementById("er_graph"));
  let st = (page - 1) * perPage.value + 1;
  let ed = Math.min((page) * perPage.value, data.value.length);
  const nodes = [];
  const edges = [];
  // left entity
  for (let i = st; i <= ed; i++) {
    nodes.push({
      name: `${pair_a.value}_${i}`,
      category: 0,
      symbolSize: 25,
      x: x_gap[perPage.value] * 2,
      y: y_gap[perPage.value] * (i - st + 1),
      label: {
        show: true,
        position: 'top',
        formatter(params) {
          return `${pair_a.value}_${i}`;
        },
      },
      tooltip: {
        formatter(params) {
          let {value} = params;
          return data.value[i - 1][Object.keys(data.value[i - 1])[0]];
        },
      }
    })
  }
  // right entity
  for (let i = st; i <= ed; i++) {
    nodes.push({
      name: `${pair_b.value}_${i}`,
      category: 0,
      symbolSize: 25,
      x: x_gap[perPage.value] * 3,
      y: y_gap[perPage.value] * (i - st + 1),
      label: {
        show: true,
        position: 'top',
        formatter(params) {
          return `${pair_b.value}_${i}`;
        },
      },
      tooltip: {
        formatter(params) {
          let {value} = params;
          return data.value[i - 1][Object.keys(data.value[i - 1])[(Object.keys(data.value[i - 1]).length + 1) / 2]];
        },
      }
    })
  }
  // align edge
  for (let i = st; i <= ed; i++) {
    edges.push({
      source: `${pair_a.value}_${i}`,
      target: `${pair_b.value}_${i}`,
      value: 3,
      lineStyle: {
        color: myPurple,
        width: 4,
      },
      tooltip: {
        formatter(params) {
          return `${data.value[i - 1][Object.keys(data.value[i - 1])[0]]} ⇔ ${data.value[i - 1][Object.keys(data.value[i - 1])[(Object.keys(data.value[i - 1]).length + 1) / 2]]}`
        }
      }
    })
  }
  const data_type = config.value["data_type"];
  if (data_type === "table") {
    // result_data.json / result_columns.json / result_categories.json
    // result_left_edges.json / result_right_edges.json
    // left value and edge
    const left_values = [];
    const left_dic = {};
    const left_type_dic = {};
    for (const item of left_edges.value) {
      const src_id = parseInt(item["source"].substring(3))
      if (src_id >= st && src_id <= ed) {
        const value = data.value[src_id - 1][`A_${item["type"]}`];
        if (Object.keys(left_dic).indexOf(value) === -1) {
          left_dic[value] = [];
          left_type_dic[value] = item["type"];
        }
        left_dic[value].push(src_id);
      }
    }
    for (let key of Object.keys(left_dic)) {
      left_values.push({
        key: key,
      })
    }
    const left_values_size = left_values.length;
    for (let i = 0; i < left_values_size; i++) {
      nodes.push({
        name: `${pair_a.value}_V_${i + 1}`,
        category: 1,
        symbolSize: 18,
        // x: (i % 2 === 0) ? 0 : (perPage.value === 5 ? 20 : 50),
        x: x_gap[perPage.value] * 1 - ((i % 2 === 0) ? x_gap[perPage.value] / 3 : 0),
        y: y_gap[perPage.value] * (ed - st + 1) * (i + 1) / left_values_size,
        label: {
          show: false,
        },
        tooltip: {
          formatter(params) {
            const item = left_values[i];
            return `${item.key}`;
          },
        }
      });
      for (let edge of left_dic[left_values[i].key]) {
        edges.push({
          source: `${pair_a.value}_${edge}`,
          target: `${pair_a.value}_V_${i + 1}`,
          value: 3,
          lineStyle: {
            width: 2,
            curveness: 0,
          },
          tooltip: {
            formatter(params) {
              return `${left_type_dic[left_values[i].key]}`
            }
          }
        });
      }
    }
    // right value and edge
    const right_values = [];
    const right_dic = {};
    const right_type_dic = {};
    for (const item of right_edges.value) {
      const src_id = parseInt(item["source"].substring(3))
      if (src_id >= st && src_id <= ed) {
        const value = data.value[src_id - 1][`B_${item["type"]}`];
        if (Object.keys(right_dic).indexOf(value) === -1) {
          right_dic[value] = [];
          right_type_dic[value] = item["type"];
        }
        right_dic[value].push(src_id)
      }
    }
    for (let key of Object.keys(right_dic)) {
      right_values.push({
        key: key,
      })
    }
    const right_values_size = right_values.length;
    for (let i = 0; i < right_values_size; i++) {
      nodes.push({
        name: `${pair_b.value}_V_${i + 1}`,
        category: 1,
        symbolSize: 18,
        // x: (i % 2 === 0) ? (perPage.value === 5 ? 300 : 1200) : (perPage.value === 5 ? 280 : 1150),
        x: x_gap[perPage.value] * 4 + ((i % 2 === 0) ? x_gap[perPage.value] / 3 : 0),
        y: y_gap[perPage.value] * (ed - st + 1) * (i + 1) / right_values_size,
        label: {
          show: false,
        },
        tooltip: {
          formatter(params) {
            const item = right_values[i];
            return `${item.key}`;
          },
        }
      });
      for (let edge of right_dic[right_values[i].key]) {
        edges.push({
          source: `${pair_b.value}_${edge}`,
          target: `${pair_b.value}_V_${i + 1}`,
          value: 3,
          lineStyle: {
            width: 2,
            curveness: 0,
          },
          tooltip: {
            formatter(params) {
              return `${right_type_dic[right_values[i].key]}`
            }
          }
        });
      }
    }
  } else {
    const left_nodes = []
    const left_nodes_dic = {}
    // 一个实体最多连接其他实体数
    const MAX_NUM = 5;
    for (let i = st; i <= ed; i++) {
      const lst = Array.from(new Set(left_edges.value[i - 1]));
      let num = 0
      for (let item of lst) {
        left_nodes.push(item);
        if (Object.keys(left_nodes_dic).indexOf(item) === -1) {
          left_nodes_dic[item] = [];
        }
        left_nodes_dic[item].push(i);
        num++;
        if (num === MAX_NUM) {
          break;
        }
      }
    }
    const left_nodes_size = left_nodes.length;
    for (let i = 0; i < left_nodes_size; i++) {
      nodes.push({
        name: `${pair_a.value}_V_${i + 1}`,
        category: 1,
        symbolSize: 18,
        // x: (i % 2 === 0) ? 0 : (perPage.value === 5 ? 20 : 50),
        x: x_gap[perPage.value] * 1 - ((i % 3) * x_gap[perPage.value] / 3),
        y: y_gap[perPage.value] * (ed - st + 1) * (i + 1) / left_nodes_size,
        label: {
          show: false,
        },
        tooltip: {
          formatter(params) {
            const item = left_nodes[i];
            return `${data.value[item]["A_name"]}`;
          },
        }
      });
      for (let j = 0; j < left_nodes_dic[left_nodes[i]].length; j++) {
        edges.push({
          source: `${pair_a.value}_${left_nodes_dic[left_nodes[i]][j]}`,
          target: `${pair_a.value}_V_${i + 1}`,
          value: 3,
          lineStyle: {
            width: 2,
            curveness: 0,
          },
          tooltip: {
            formatter(params) {
              return ""
            }
          }
        });
      }
    }
    const right_nodes = []
    const right_nodes_dic = {}
    for (let i = st; i <= ed; i++) {
      const lst = Array.from(new Set(right_edges.value[i - 1]));
      let num = 0;
      for (let item of lst) {
        right_nodes.push(item);
        if (Object.keys(right_nodes_dic).indexOf(item) === -1) {
          right_nodes_dic[item] = [];
        }
        right_nodes_dic[item].push(i);
        num++;
        if (num === MAX_NUM) {
          break;
        }
      }
    }
    const right_nodes_size = right_nodes.length;
    for (let i = 0; i < right_nodes_size; i++) {
      nodes.push({
        name: `${pair_b.value}_V_${i + 1}`,
        category: 1,
        symbolSize: 18,
        // x: (i % 2 === 0) ? (perPage.value === 5 ? 300 : 1200) : (perPage.value === 5 ? 280 : 1150),
        x: x_gap[perPage.value] * 4 + ((i % 3) * x_gap[perPage.value] / 3),
        y: y_gap[perPage.value] * (ed - st + 1) * (i + 1) / right_nodes_size,
        label: {
          show: false,
        },
        tooltip: {
          formatter(params) {
            const item = right_nodes[i];
            return `${data.value[item]["B_name"]}`;
          },
        }
      });
      for (let j = 0; j < right_nodes_dic[right_nodes[i]].length; j++) {
        edges.push({
          source: `${pair_b.value}_${right_nodes_dic[right_nodes[i]][j]}`,
          target: `${pair_b.value}_V_${i + 1}`,
          value: 3,
          lineStyle: {
            width: 2,
            curveness: 0,
          },
          tooltip: {
            formatter(params) {
              return ""
            }
          }
        });
      }
    }
  }
  if (categories.value.length === 1) {
    categories.value.push({"name": "neighbor entity"});
  }
  graph_option.value = {
    tooltip: {},
    animationDurationUpdate: 1500,
    animationEasingUpdate: 'quinticInOut',
    legend: [{
      left: 'center',
      textStyle: {
        fontSize: 15,
      },
      data: data_type === "table" ? (categories.value.map(function (a) {
        return {
          name: a.name,
        }
      })) : (categories.value.map(function (a) {
        return {
          name: a.name,
        }
      })),
    }],
    series: [{
      type: 'graph',
      zoom: 1.1,
      layout: "none",
      roam: true,
      label: {
        show: true,
        position: 'top',
        formatter: params => params.data.name,
      },
      draggable: true,
      data: nodes,
      links: edges,
      categories: categories.value,
      force: {
        edgeLength: [10, 200],
        repulsion: 1200,
        gravity: 0.6
      },
    }]
  };
  graph.value.setOption(graph_option.value)
  graph.value.resize()
}
onMounted(() => {
  render(curPage.value);
});
</script>

<style scoped>
#graph {
  width: 100%;
  /*border: 1px solid rgb(24, 160, 88);*/
}

.z-table-pair {
  text-align: center;
  font-weight: bold;
  color: white;
}


/*:deep(#er_graph>div){*/
/*  width: 100%!important;*/
/*}*/
/*:deep(#er_graph>div>canvas){*/
/*  width: 100%!important;*/
/*}*/
:deep(table){
  table-layout: fixed;
  width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}



/* TODO 截图 */

/* if sys_config.jietu */
/* :deep(td){
  padding: 2px 12px;
}
:deep(th){
  padding: 2px 12px;
} */
/* else */
:deep(.n-table td) {
  padding-top: 9px;
  padding-bottom: 9px;
}
</style>