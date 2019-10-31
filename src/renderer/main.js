import Vue from 'vue'

import App from './App'
import router from './router'
import store from './store'

Vue.config.productionTip = false

router.afterEach((to, from) => {
  document.title = to.meta.title || "";
});

/* eslint-disable no-new */
new Vue({
  components: { App },
  router,
  store,
  template: '<App/>'
}).$mount('#app')
