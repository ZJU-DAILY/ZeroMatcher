import {createApp} from 'vue'
import App from './App.vue'
import router from "./router";
import {config} from "./config";
// import * as echarts from "echarts";
import "./index.css";

import {
    create,
    NGrid,
    NGridItem,
    NMenu,
    NSpace,
    NSteps,
    NStep,
    NButtonGroup,
    NButton,
    NRadioGroup,
    NRadioButton,
    NIcon,
    NTabs,
    NTabPane,
    NTag,
    NH3,
    NH2,
    NH1,
    NTable,
    NTooltip,
    NPagination,
    NUpload,
    NUploadDragger,
    NP,
    NText,
    NForm,
    NFormItem,
    NInput,
    NRadio,
    NSwitch,
    NDivider,
    NInputNumber,
    NCheckboxGroup,
    NCheckbox,
    NMessageProvider,
    NEllipsis,
    NCard,
    NModal,
    NDialogProvider,
    NDialog,
} from 'naive-ui'

const naive = create({
    components: [
        NGrid,
        NGridItem,
        NMenu,
        NSpace,
        NSteps,
        NStep,
        NButtonGroup,
        NButton,
        NRadioGroup,
        NRadioButton,
        NIcon,
        NTabs,
        NTabPane,
        NTag,
        NH3,
        NH2,
        NH1,
        NTable,
        NTooltip,
        NPagination,
        NUpload,
        NUploadDragger,
        NP,
        NText,
        NForm,
        NFormItem,
        NInput,
        NRadio,
        NSwitch,
        NDivider,
        NInputNumber,
        NCheckboxGroup,
        NCheckbox,
        NMessageProvider,
        NEllipsis,
        NCard,
        NModal,
        NDialogProvider,
        NDialog,
    ]
})

document.title = config.title;
const app = createApp(App);
// app.config.globalProperties.$echarts = echarts;
app.use(router);
app.use(naive);
app.mount('#app')
