import Vue from 'vue'
import Router from 'vue-router'

Vue.use(Router)

export default new Router({
  routes: [
    {
      path: '/landing',
      name: 'landing-page',
      component: require('@/components/LandingPage').default,
      meta: {
        title: 'Color Search'
      }
    },
    {
      path: '/color-picker',
      name: 'color-picker',
      component: require('@/components/ColorPicker').default,
      meta: {
        title: 'Color Picker'
      }
    },
    {
      path: '*',
      redirect: to => {
        const {hash} = to;
        switch (hash) {
          case "#color-picker": return "/color-picker";
          default: return "/landing";
        }
      }
    }
  ]
})
