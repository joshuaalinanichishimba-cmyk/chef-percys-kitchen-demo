<script setup lang="ts">
import { ref } from 'vue'
import { money } from './cart'

type Booking = {
  reference: string
  event_date: string
  guests: number
  status: 'received' | 'quoted' | 'booked' | 'completed' | 'cancelled'
  quote_ngwee: number | null
  deposit_ngwee: number | null
  paid_ngwee: number
  quote_notes: string
}
const labels = {
  received: 'Inquiry received', quoted: 'Quote available', booked: 'Booking confirmed',
  completed: 'Event completed', cancelled: 'Inquiry cancelled',
}
const reference = ref('')
const booking = ref<Booking | null>(null)
const error = ref('')
const busy = ref(false)
let retry: { body: string; reference: string } | null = null

async function request(path: string, init?: RequestInit) {
  if (busy.value) return false
  busy.value = true
  error.value = ''
  try {
    const response = await fetch(path, init)
    const result = await response.json()
    if (!response.ok) throw new Error(typeof result.detail === 'string'
      ? result.detail : 'Check the reference or inquiry details and try again.')
    booking.value = result
    reference.value = result.reference
    return true
  } catch (issue) {
    error.value = issue instanceof Error ? issue.message : 'Request failed.'
    return false
  } finally {
    busy.value = false
  }
}

async function submit(event: Event) {
  const form = event.currentTarget as HTMLFormElement
  const data = Object.fromEntries(new FormData(form))
  const payload = { ...data, guests: Number(data.guests) }
  const body = JSON.stringify(payload)
  if (retry?.body !== body) retry = { body, reference: crypto.randomUUID() }
  const sent = await request('/api/catering', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ...payload, reference: retry.reference }),
  })
  if (sent) {
    form.reset()
    retry = null
  }
}

function lookup() {
  booking.value = null
  return request('/api/catering/' + encodeURIComponent(reference.value.trim()))
}
</script>

<template>
  <section class="checkout" aria-labelledby="inquiry-title">
    <h2 id="inquiry-title">Request a catering quote</h2>
    <form @submit.prevent="submit">
      <fieldset :disabled="busy">
        <label>Name <input name="customer_name" autocomplete="name" maxlength="120" required></label>
        <label>Phone <input name="phone" type="tel" autocomplete="tel" maxlength="24" required></label>
        <label>Event date <input name="event_date" type="date" required></label>
        <label>Guests <input name="guests" type="number" min="1" max="10000" required></label>
        <label>Venue <input name="venue" maxlength="200" required></label>
        <label>Event details <textarea name="details" maxlength="800"></textarea></label>
        <button class="button" type="submit">Send inquiry</button>
      </fieldset>
    </form>
  </section>
  <section class="checkout" aria-labelledby="booking-title">
    <h2 id="booking-title">Check your catering inquiry</h2>
    <form @submit.prevent="lookup">
      <label>Catering reference <input v-model="reference" maxlength="36" required></label>
      <button class="button" :disabled="busy" type="submit">Check status</button>
    </form>
    <p v-if="error" role="alert">{{ error }}</p>
    <div v-if="booking" role="status">
      <p><strong>{{ labels[booking.status] }}</strong> · {{ booking.event_date }} · {{ booking.guests }} guests</p>
      <p>Save this reference to check your status later: {{ booking.reference }}</p>
      <template v-if="booking.quote_ngwee !== null">
        <p>Quote {{ money(booking.quote_ngwee) }} · Deposit {{ money(booking.deposit_ngwee ?? 0) }}</p>
        <p>Payment recorded by Percy {{ money(booking.paid_ngwee) }} · Balance {{ money(booking.quote_ngwee - booking.paid_ngwee) }}</p>
        <p v-if="booking.quote_notes">{{ booking.quote_notes }}</p>
      </template>
    </div>
  </section>
</template>
