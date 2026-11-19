import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createRouter, createWebHashHistory } from 'vue-router'
import App from './App.vue'
import Kitchen from './Kitchen.vue'
import Menu from './Menu.vue'
import './style.css'

const pages = ['home', 'food', 'catering', 'about', 'contact']
const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/menu', name: 'menu', component: Menu },
    ...pages.map(page => ({ path: page === 'home' ? '/' : '/' + page, name: page, component: Kitchen, props: { page } })),
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
  scrollBehavior: () => ({ top: 0 }),
})

createApp(App).use(createPinia()).use(router).mount('#app')
