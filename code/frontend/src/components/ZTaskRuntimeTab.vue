<template>
  <n-grid :cols="48">
    <n-gi :span="12">
      <n-card title="Monitor" class="z-card">
        <div style="height: 193px;">
          <canvas id="cpu_load_zxt" style="width: 100%; height: 100%;"></canvas>
        </div>
        <div style="height: 193px">
          <canvas id="gpu_load_zxt" style="width: 100%; height: 100%;"></canvas>
        </div>
        <div style="height: 194px">
          <canvas id="gpu_mem_zxt" style="width: 100%; height: 100%;"></canvas>
        </div>
      </n-card>
    </n-gi>
    <n-gi :offset="sys_config.jietu?0:1" :span="sys_config.jietu?12:35">
      <n-card title="Logs" class="z-card">
        <div id="log_text" style="height:580px;"></div>
      </n-card>
    </n-gi>
  </n-grid>
</template>
<script setup>
import {useRoute} from "vue-router";
import Chart from "chart.js/auto";
import {config as sys_config} from "../config";
import moment from "moment";
import {onMounted, ref, defineEmits, inject} from "vue";
import {client, localClient} from "../http";

const emit = defineEmits(["on-finish"])
const route = useRoute();
const cpu_gpu_ws = ref({});
const log_ws = ref({});
const config = inject("config");
const draw_cpu_gpu_zxt = () => {
  const dt = new Date()
  const time = [
    `${dt.getHours()}:${dt.getMinutes()}:${dt.getSeconds()}`
  ];
  const titles = ["CPU Load", "GPU Load", "GPU Memory"]
  const zxt_data = [[0], [0], [0]]
  const zxt_eles = [
    document.getElementById('cpu_load_zxt'),
    document.getElementById('gpu_load_zxt'),
    document.getElementById('gpu_mem_zxt'),
  ];
  const zxts = []
  for (let i = 0; i < 3; i++) {
    zxts[i] = new Chart(zxt_eles[i], {
      type: 'line',
      data: {
        labels: time,
        datasets: [{
          label: titles[i],
          data: zxt_data[i],
          fill: true,
          borderColor: 'rgb(24, 160, 88)',
          tension: 0.4,
        }]
      },
      options: {
        scales: {
          x:{
            ticks:{
              font: {
                size: 18,
              }
            }
          },
          y: {
            min: 0,
            max: 100,
            ticks:{
              font: {
                size: 18,
              }
            }
          },
        },
        plugins: {
          title: {
            display: false,
          },
          legend: {
            display: true,
            labels:{
              font:{
                size: 18,
              }
            }
          }
        },
      }
    });
  }
  let random=(m,n,float)=>{
    return Math.random()*(m-n)+n
  }
  let n=sys_config.jietu?3:4;
  cpu_gpu_ws.value = new WebSocket(sys_config.baseWs + "/task/cpu_gpu")
  cpu_gpu_ws.value.onopen = () => {
    console.log('ws连接状态：' + cpu_gpu_ws.value.readyState);
    cpu_gpu_ws.value.send(JSON.stringify({
      task_id: route.params.id,
    }));
  }
  cpu_gpu_ws.value.onmessage = (data) => {
    if (time.length >= n) {
      for (let i = 0; i < n-1; i++) {
        zxt_data[0][i] = zxt_data[0][i + 1];
        zxt_data[1][i] = zxt_data[1][i + 1];
        zxt_data[2][i] = zxt_data[2][i + 1];
      }
      time.shift();
    }
    // cpu load/gpu load/gpu mem
    let json_data = JSON.parse(data.data);
    time.push(json_data["time"])
    let cpu_load_mx = json_data["cpu_load"] > 50 ? 100 : 50;
    let gpu_load_mx = json_data["gpu_load"] > 50 ? 100 : 50;
    let gpu_mem_mx = json_data["gpu_mem"] > 50 ? 100 : 50;
    if (time.length >= n) {
      zxt_data[0][n-1] = json_data["cpu_load"];
      zxt_data[1][n-1] = json_data["gpu_load"];
      zxt_data[2][n-1] = json_data["gpu_mem"];
    } else {
      zxt_data[0].push(json_data["cpu_load"]);
      zxt_data[1].push(json_data["gpu_load"]);
      zxt_data[2].push(json_data["gpu_mem"]);
    }
    zxts[0].options.scales.y.max = cpu_load_mx;
    zxts[1].options.scales.y.max = gpu_load_mx;
    zxts[2].options.scales.y.max = gpu_mem_mx;
    zxts[0].update();
    zxts[1].update();
    zxts[2].update();

  }
  cpu_gpu_ws.value.onclose = () => {
    console.log('ws连接状态：' + cpu_gpu_ws.value.readyState);
  }
  cpu_gpu_ws.value.onerror = function (error) {
    console.log(error);
  }
};
const getLog = async () => {
  let task_id = route.params.id;
  const dv = document.getElementById('log_text');
  dv.innerHTML=""
  log_ws.value = new WebSocket(sys_config.baseWs + "/task/log")
  log_ws.value.onopen = () => {
    console.log('log ws连接状态：' + log_ws.value.readyState);
    log_ws.value.send(JSON.stringify({
      task_id: route.params.id,
    }));
  }
  log_ws.value.onmessage = (data) => {
    let logs = JSON.parse(data.data)
    if (logs.length > 0) {
      // console.log(logs)
      for (let i = 0; i < logs.length; i++) {
        let str = "";
        let infos = logs[i].split(/\|/)
        let arr = infos[2].split("-");
        if(arr.length===2){
          infos[2] = arr[0];
          infos.push(arr[1]);
        }
        let len = infos.length;
        str += "<span style='color:teal;'>" + infos[0] + "</span>";
        if (len > 1) {
          str += " - <span style='color:goldenrod'>" + infos[1] + "</span>";
          if (len > 2) {
            str += " - <span style='color:rebeccapurple'>" + infos[2] + "</span>";
            if (len > 3) {
              str += " - <span style='color:gray'>" + infos[3] + "</span>";
              if (len > 4) {
                str += " - <span style='color:rgba(24,160,88,0.85)'>" + infos[4] + "</span>";
                if (len > 5) {
                  str += " - <span style='color:black'>" + infos[5] + "</span>";
                }
              }
            }
          }
        }
        str += "</br>"
        if (len > 2 && infos[2].trim("\n") === "END") {
          // result emit
          emit("on-finish");
          log_ws.value.close()
        }
        const dv = document.getElementById('log_text');
        dv.innerHTML += str;
        dv.scrollTop = dv.scrollHeight;
      }
    }
  }
  log_ws.value.onclose = () => {
    console.log('ws连接状态：' + log_ws.value.readyState);
  }
  log_ws.value.onerror = function (error) {
    console.log(error);
  }
};
onMounted(() => {
  draw_cpu_gpu_zxt();
  getLog();
});
// onbeforeunload(()=>{
//   if(log_ws.value){
//     log_ws.value.close();
//   }
//   if(cpu_gpu_ws.value){
//     cpu_gpu_ws.value.close();
//   }
// })
</script>

<style scoped>
#log_text {
  /*border: 1px solid rgb(24, 160, 88);*/
  font-size: 18px;
  overflow: auto;
  /*padding: 0.5rem;*/
}
</style>