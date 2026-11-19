<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { money, orderHistory } from './cart'

type Receipt = {
  reference: string
  status: keyof typeof labels
  fulfillment: 'pickup' | 'delivery'
  total_ngwee: number
  items: { name: string; option: string; quantity: number; unit_price_ngwee: number }[]
}
const labels = {
  received: 'Request received', confirmed: 'Order confirmed', preparing: 'Being prepared',
  ready: 'Order ready', completed: 'Order completed', cancelled: 'Order cancelled',
}
const route = useRoute()
const router = useRouter()
const reference = ref('')
const history = orderHistory()
const receipt = ref<Receipt | null>(null)
const status = ref('')

const attempt = ref(0)
watch([() => route.query.reference, attempt], async ([value], _, onCleanup) => {
  const request = new AbortController()
  onCleanup(() => request.abort())
  reference.value = typeof value === 'string' ? value : ''
  receipt.value = null
  status.value = ''
  if (!reference.value) return
  status.value = 'Looking up your order…'
  try {
    const response = await fetch('/api/orders/' + encodeURIComponent(reference.value), { signal: request.signal })
    if (!response.ok) throw new Error(response.status === 404 || response.status === 422
      ? 'Order reference not found.' : 'Could not look up this order.')
    const data = await response.json()
    if (!request.signal.aborted) {
      receipt.value = data
      status.value = ''
    }
  } catch (error) {
    if (!request.signal.aborted) status.value = error instanceof Error ? error.message : 'Could not look up this order.'
  }
}, { immediate: true })
</script>

<template>
  <main class="wrap section inside" tabindex="-1">
    <h1>Orders</h1>
    <form class="checkout" @submit.prevent="router.push({ name: 'orders', query: { reference: reference.trim() } })">
      <label>Order reference <input v-model="reference" required maxlength="36"></label>
      <button type="submit" class="button">Find order</button>
    </form>
    <p v-if="status" role="status">{{ status }}</p>
    <section v-if="receipt" class="checkout" aria-labelledby="receipt-title">
      <h2 id="receipt-title">{{ labels[receipt.status] }}</h2>
      <button type="button" class="text-link" @click="attempt++">Refresh status</button>
      <p>Reference <strong>{{ receipt.reference }}</strong></p>
      <ul>
        <li v-for="(line, index) in receipt.items" :key="index">
          {{ line.quantity }} × {{ line.name }} {{ line.option }} · {{ money(line.quantity * line.unit_price_ngwee) }}
        </li>
      </ul>
      <p><strong>Food subtotal {{ money(receipt.total_ngwee) }}</strong></p>
      <p>{{ receipt.fulfillment === 'pickup' ? 'Pickup at L237, CBU Campus.' : 'Yango delivery requested.' }} <span v-if="receipt.status === 'received'">Percy will confirm availability and payment arrangements.</span></p>
    </section>
    <section v-if="history.length" class="checkout" aria-labelledby="history-title">
      <h2 id="history-title">Recent orders on this browser</h2>
      <ul>
        <li v-for="id in history" :key="id"><RouterLink class="text-link" :to="{ name: 'orders', query: { reference: id } }">{{ id }}</RouterLink></li>
      </ul>
    </section>
  </main>
</template>
