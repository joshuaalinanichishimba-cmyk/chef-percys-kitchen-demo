<script setup lang="ts">
import { nextTick, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { location, whatsapp } from './kitchen'

const route = useRoute()
const open = ref(false)
const navigation = [
  { name: 'home', label: 'Home' }, { name: 'food', label: 'Our food' },
  { name: 'menu', label: 'Menu' },
  { name: 'orders', label: 'Orders' },
  { name: 'recipes', label: 'Recipes' },
  { name: 'catering', label: 'Catering' }, { name: 'about', label: 'Meet Percy' },
  { name: 'contact', label: 'Contact' },
]
watch(() => route.name, async name => {
  open.value = false
  const page = navigation.find(item => item.name === name)
  document.title = page?.name === 'home' ? 'Chèf Percy’s Kitchen | Platters that matter' : page?.label + ' | Chèf Percy’s Kitchen'
  await nextTick()
  document.querySelector<HTMLElement>('main')?.focus({ preventScroll: true })
})
</script>

<template>
  <header class="site-header">
    <div class="wrap header-inner">
      <RouterLink to="/" class="brand" aria-label="Chèf Percy’s Kitchen home" @click="open = false">
        <img src="/images/logo.webp" width="52" height="52" alt="">
        <span>CHÈF PERCY’S <small>KITCHEN</small></span>
      </RouterLink>
      <button class="menu-toggle" type="button" aria-controls="site-nav" :aria-expanded="open" @click="open = !open">{{ open ? 'Close' : 'Menu' }}</button>
      <nav id="site-nav" :class="{ open }" aria-label="Main navigation">
        <RouterLink v-for="item in navigation" :key="item.name" :to="{ name: item.name }" @click="open = false">{{ item.label }}</RouterLink>
      </nav>
      <a class="button nav-order" :href="whatsapp('Hi Chef Percy, I’d like to ask about a pre-order.')">Pre-order on WhatsApp</a>
    </div>
  </header>
  <RouterView />
  <footer class="site-footer">
    <div class="wrap footer-inner">
      <RouterLink to="/" class="brand"><img src="/images/logo.webp" width="52" height="52" alt=""><span>CHÈF PERCY’S <small>KITCHEN</small></span></RouterLink>
      <p>{{ location }}</p>
      <RouterLink to="/contact">Contact the kitchen</RouterLink>
    </div>
  </footer>
</template>
