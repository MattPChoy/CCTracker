import { createApp } from "vue";
import { createRouter, createWebHistory } from "vue-router";
import App from "./App.vue";
import Home from "./views/Home.vue";
import Boards from "./views/Boards.vue";
import BoardView from "./views/BoardView.vue";
import "./style.css";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", component: Home },
    { path: "/boards", component: Boards },
    { path: "/boards/:id", component: BoardView, props: true },
  ],
});

createApp(App).use(router).mount("#app");
