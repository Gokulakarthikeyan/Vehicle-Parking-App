import { createApp } from "vue";
import App from "./App.vue";
import router from "./router";

import Toast from "vue-toastification";
import "vue-toastification/dist/index.css";

const app = createApp(App);
app.use(router);
app.use(Toast, {
  // you can add default options here, e.g.:
  timeout: 2000,
  position: "top-right",
});
app.mount("#app");
