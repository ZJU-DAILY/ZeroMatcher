import {createRouter, createWebHistory} from "vue-router";
import {config as sys_config} from "./config"

const routes = [
    {
        path: "/",
        name: "home",
        // component: () => sys_config.jietu? import("./pages/Home_jietu.vue"):  import("./pages/Home.vue"),
        component: () => import("./pages/Home.vue"),
    },
    {
        path: "/detail/:id/:demo?",
        name: "detail",
        component: () => import("./pages/Detail.vue"),
    }
]
const router = createRouter({
    history: createWebHistory(),
    routes,
});
export default router;