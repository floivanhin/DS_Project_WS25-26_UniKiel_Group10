import { createRouter, createWebHistory } from "vue-router";
import MainPage from "../pages/MainPage.vue";
import RQ1Page from "../pages/RQ1Page.vue";
import RQ2Page from "../pages/RQ2Page.vue";
import RQ3Page from "../pages/RQ3Page.vue";
import RQ4Page from "../pages/RQ4Page.vue";
import RQ5Page from "../pages/RQ5Page.vue";
import RQ6Page from "../pages/RQ6Page.vue";
import RQ7Page from "../pages/RQ7Page.vue";
import RQ8Page from "../pages/RQ8Page.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", name: "main", component: MainPage },
    { path: "/rq1", name: "rq1", component: RQ1Page },
    { path: "/rq2", name: "rq2", component: RQ2Page },
    { path: "/rq3", name: "rq3", component: RQ3Page },
    { path: "/rq4", name: "rq4", component: RQ4Page },
    { path: "/rq5", name: "rq5", component: RQ5Page },
    { path: "/rq6", name: "rq6", component: RQ6Page },
    { path: "/rq7", name: "rq7", component: RQ7Page },
    { path: "/rq8", name: "rq8", component: RQ8Page },
  ],
});

export default router;
