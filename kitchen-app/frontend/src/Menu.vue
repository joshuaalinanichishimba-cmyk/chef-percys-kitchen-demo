<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import Checkout from './Checkout.vue'
import { money, useCart } from './cart'
import { whatsapp } from './kitchen'

type Entry = {
  id: number
  category: string
  name: string
  option: string
  description: string
  price_ngwee: number
  max_price_ngwee: number | null
  starting_at: boolean
}

const cart = useCart()
const menu = ref<Entry[]>([])
const state = ref<'loading' | 'ready' | 'error'>('loading')
const categories = computed(() => [...new Set(menu.value.map(entry => entry.category))])

function price(entry: Entry) {
  if (entry.starting_at) return 'From ' + money(entry.price_ngwee)
  if (entry.max_price_ngwee !== null) return money(entry.price_ngwee) + '–' + money(entry.max_price_ngwee)
  return money(entry.price_ngwee)
}

async function loadMenu() {
  state.value = 'loading'
  try {
    const response = await fetch('/api/menu')
    if (!response.ok) throw new Error('Menu unavailable')
    const data: unknown = await response.json()
    if (!Array.isArray(data)) throw new Error('Invalid menu response')
    menu.value = data
    state.value = 'ready'
  } catch {
    state.value = 'error'
  }
}

onMounted(loadMenu)
</script>

<template>
  <main class="wrap section inside" tabindex="-1">
    <p class="eyebrow">CHÈF PERCY’S KITCHEN</p>
    <h1>Menu</h1>
    <p>Pre-order in advance. Slots are limited, and advance payment secures your slot. Ask Percy about pickup at CBU or delivery via Yango.</p>
    <p v-if="state === 'loading'" role="status">Loading menu…</p>
    <div v-else-if="state === 'error'">
      <p role="status">The menu couldn’t be loaded. Ask Percy for today’s availability.</p>
      <button type="button" class="text-link" @click="loadMenu">Try again</button>
    </div>
    <p v-else-if="!categories.length">No menu items are listed right now.</p>
    <section v-for="category in categories" :key="category" class="menu-category">
      <h2>{{ category }}</h2>
      <ul>
        <li v-for="entry in menu.filter(item => item.category === category)" :key="entry.id">
          <div>
            <strong>{{ entry.name }}</strong>
            <span v-if="entry.option"> · {{ entry.option }}</span>
            <p v-if="entry.description">{{ entry.description }}</p>
          </div>
          <div class="menu-action">
            <strong>{{ price(entry) }}</strong>
            <button v-if="!entry.starting_at && entry.max_price_ngwee === null"
              class="button" type="button" :aria-label="'Add ' + entry.name + ' ' + entry.option"
              :disabled="cart.submitting || (cart.lines.find(line => line.id === entry.id)?.quantity ?? 0) >= 20 || (cart.lines.length >= 30 && !cart.lines.some(line => line.id === entry.id))"
              @click="cart.add(entry)">Add</button>
          </div>
        </li>
      </ul>
    </section>
    <Checkout @refresh-menu="loadMenu" />
    <a class="button after-grid" :href="whatsapp('Hi Chef Percy, I’d like to ask about a pre-order or catering quote.')">Message Percy on WhatsApp</a>
  </main>
</template>
