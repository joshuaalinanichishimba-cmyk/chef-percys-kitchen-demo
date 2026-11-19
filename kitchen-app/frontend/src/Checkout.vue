<script setup lang="ts">
import { ref } from 'vue'
import { money, rememberOrder, useCart } from './cart'

const emit = defineEmits<{ refreshMenu: [] }>()
const cart = useCart()
const fulfillment = ref('pickup')
const error = ref('')
const confirmation = ref('')
let retry: { body: string; reference: string } | null = null

async function submit(event: Event) {
  if (cart.submitting || !cart.lines.length) return
  cart.submitting = true
  error.value = ''
  confirmation.value = ''
  try {
    const fields = new FormData(event.currentTarget as HTMLFormElement)
    const data = Object.fromEntries(fields)
    if (data.fulfillment === 'pickup') data.address = ''
    const payload = {
      ...data,
      lines: cart.lines.map(line => ({
        menu_id: line.id, quantity: line.quantity, expected_price_ngwee: line.price_ngwee,
      })),
    }
    const body = JSON.stringify(payload)
    if (retry?.body !== body) retry = { body, reference: crypto.randomUUID() }
    const response = await fetch('/api/orders', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...payload, reference: retry.reference }),
    })
    const result = await response.json()
    if (!response.ok) {
      if (response.status === 409) emit('refreshMenu')
      throw new Error(typeof result.detail === 'string' ? result.detail : 'Check your order details and phone number.')
    }
    confirmation.value = result.reference
    rememberOrder(result.reference)
    cart.lines = []
    retry = null
  } catch (problem) {
    error.value = problem instanceof Error ? problem.message : 'Could not send the order. Try again.'
  } finally {
    cart.submitting = false
  }
}
</script>

<template>
  <section class="checkout" aria-labelledby="order-title">
    <h2 id="order-title">Your order</h2>
    <p v-if="confirmation" role="status">Request received. <RouterLink class="text-link" :to="{ name: 'orders', query: { reference: confirmation } }">View confirmation</RouterLink></p>
    <p v-if="!cart.count && !confirmation">Add items from the menu to start an order.</p>
    <form v-if="cart.count" @submit.prevent="submit">
      <fieldset :disabled="cart.submitting">
        <ul class="cart-lines">
          <li v-for="line in cart.lines" :key="line.id">
            <span>{{ line.name }} {{ line.option }}</span>
            <button type="button" class="button" :aria-label="'Decrease ' + line.name" @click="cart.adjust(line.id, -1)">−</button>
            <span>{{ line.quantity }}</span>
            <button type="button" class="button" :aria-label="'Increase ' + line.name" :disabled="line.quantity >= 20" @click="cart.adjust(line.id, 1)">+</button>
          </li>
        </ul>
        <p><strong>Food subtotal {{ money(cart.total) }}</strong></p>
        <label>Name <input name="customer_name" autocomplete="name" maxlength="120" required></label>
        <label>Phone <input name="phone" type="tel" autocomplete="tel" maxlength="24" required></label>
        <label>Collection
          <select name="fulfillment" v-model="fulfillment">
            <option value="pickup">Pickup at L237, CBU Campus</option>
            <option value="delivery">Request Yango delivery</option>
          </select>
        </label>
        <label v-if="fulfillment === 'delivery'">Delivery address
          <textarea name="address" autocomplete="street-address" maxlength="400" required></textarea>
        </label>
        <p>Percy will confirm availability and payment arrangements. Delivery fees are confirmed separately.</p>
        <button type="submit" class="button">{{ cart.submitting ? 'Sending…' : 'Send order request' }}</button>
      </fieldset>
    </form>
    <p v-if="error" role="alert">{{ error }}</p>
  </section>
</template>
