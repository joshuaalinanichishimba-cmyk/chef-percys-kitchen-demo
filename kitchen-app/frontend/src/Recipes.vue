<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { money } from './cart'
import { whatsapp } from './kitchen'

type Product = { id: number; title: string; description: string; kind: 'recipe' | 'cookbook'; price_ngwee: number }
const items = ref<Product[]>([])
const loading = ref(true)
const catalogueError = ref(false)
const token = ref('')
const result = ref('')
const working = ref(false)

async function load() {
  loading.value = true
  catalogueError.value = false
  try {
    const response = await fetch('/api/digital')
    if (!response.ok) throw new Error()
    items.value = await response.json()
  } catch {
    catalogueError.value = true
  } finally {
    loading.value = false
  }
}

async function download() {
  working.value = true
  result.value = ''
  try {
    const response = await fetch('/api/digital/download', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token: token.value.trim().toLowerCase() }),
    })
    if (!response.ok) {
      throw new Error(response.status === 404 || response.status === 422
        ? 'Check the download code or ask Percy for a replacement.' : 'Download unavailable. Try again.')
    }
    const url = URL.createObjectURL(await response.blob())
    const link = document.createElement('a')
    link.href = url
    link.download = 'chef-percy.pdf'
    document.body.append(link)
    link.click()
    link.remove()
    setTimeout(() => URL.revokeObjectURL(url), 30000)
    result.value = 'Download started.'
  } catch (error) {
    result.value = error instanceof Error ? error.message : 'Download unavailable.'
  } finally {
    working.value = false
  }
}
onMounted(load)
</script>

<template>
  <main class="wrap section inside" tabindex="-1">
    <h1>Recipes &amp; cookbooks</h1>
    <p>Buy a PDF from Percy on WhatsApp. Once Percy verifies your payment, he’ll send a download code.</p>
    <p v-if="loading" role="status">Loading the catalogue…</p>
    <p v-else-if="catalogueError">The catalogue is unavailable. <button type="button" class="text-link" @click="load">Try again</button></p>
    <p v-else-if="!items.length">No recipes or cookbooks are available yet.</p>
    <section v-for="item in items" :key="item.id" class="checkout">
      <h2>{{ item.title }}</h2>
      <p>{{ item.kind === 'recipe' ? 'Recipe PDF' : 'Cookbook PDF' }} · {{ money(item.price_ngwee) }}</p>
      <p>{{ item.description }}</p>
      <a class="button" :href="whatsapp('Hi Chef Percy, I would like to buy ' + item.title + ' (' + money(item.price_ngwee) + ').')">Buy on WhatsApp</a>
    </section>
    <form class="checkout" @submit.prevent="download">
      <h2>Download a purchase</h2>
      <label>Download code <input v-model="token" autocomplete="off" spellcheck="false" maxlength="64" required></label>
      <button type="submit" class="button" :disabled="working">{{ working ? 'Downloading…' : 'Download PDF' }}</button>
      <p v-if="result" role="status">{{ result }}</p>
    </form>
  </main>
</template>
