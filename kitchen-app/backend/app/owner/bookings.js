const list = document.querySelector('#bookings')
const bookingStatus = document.querySelector('#bookings-status')
const paymentForm = document.querySelector('#record-payment')
const paymentStatus = document.querySelector('#payment-status')
const paymentList = document.querySelector('#payment-list')
const money = new Intl.NumberFormat('en-ZM', { style: 'currency', currency: 'ZMW' })

async function request(path, method = 'GET', data) {
  const response = await fetch('/owner/api/' + path, {
    method,
    headers: { 'Content-Type': 'application/json', 'X-Owner-Action': 'menu-edit' },
    body: data === undefined ? undefined : JSON.stringify(data),
  })
  const result = await response.json()
  if (!response.ok) throw new Error(typeof result.detail === 'string' ? result.detail : 'Check the details and try again.')
  return result
}

function text(tag, value) {
  const element = document.createElement(tag)
  element.textContent = value
  return element
}

function quoteField(labelText, name, initial, type) {
  const label = text('label', labelText)
  const input = document.createElement(type === 'textarea' ? 'textarea' : 'input')
  input.name = name
  input.value = initial
  if (type === 'textarea') input.maxLength = 800
  else {
    input.type = 'number'
    input.step = '0.01'
    input.min = name === 'deposit' ? '0' : '0.01'
    input.max = '1000000'
    input.required = true
  }
  label.append(input)
  return label
}

function renderBooking(item) {
  const row = document.createElement('li')
  const path = 'catering/' + encodeURIComponent(item.reference)
  row.append(
    text('strong', item.customer_name + ' · ' + item.phone),
    text('p', item.event_date + ' · ' + item.guests + ' guests · ' + item.venue),
    text('p', item.details),
    text('small', item.reference),
    text('p', 'Status: ' + item.status + ' · Recorded payments: ' + money.format(item.paid_ngwee / 100)),
  )
  if (item.quote_ngwee !== null) {
    row.append(text('p', 'Quoted ' + money.format(item.quote_ngwee / 100) +
      ' · Deposit ' + money.format(item.deposit_ngwee / 100)))
  }
  if (item.status === 'received' || item.status === 'quoted') {
    const form = document.createElement('form')
    form.append(
      quoteField('Quote (K)', 'quote', item.quote_ngwee === null ? '' : item.quote_ngwee / 100, 'number'),
      quoteField('Deposit (K)', 'deposit', (item.deposit_ngwee ?? 0) / 100, 'number'),
      quoteField('Customer-facing quote notes', 'notes', item.quote_notes, 'textarea'),
    )
    const submit = text('button', 'Save quote')
    submit.type = 'submit'
    form.append(submit)
    form.addEventListener('submit', async event => {
      event.preventDefault()
      const data = new FormData(form)
      submit.disabled = true
      try {
        await request(path + '/quote', 'PUT', {
          quote_ngwee: Math.round(Number(data.get('quote')) * 100),
          deposit_ngwee: Math.round(Number(data.get('deposit')) * 100),
          quote_notes: data.get('notes'),
        })
        await refresh()
      } catch (error) {
        bookingStatus.textContent = error.message
      } finally {
        submit.disabled = false
      }
    })
    row.append(form)
  }
  const actions = document.createElement('div')
  actions.className = 'order-actions'
  const transitions = {
    received: [['cancelled', 'Cancel inquiry']],
    quoted: [['booked', 'Confirm booking'], ['cancelled', 'Cancel inquiry']],
    booked: [['completed', 'Complete booking'], ['cancelled', 'Cancel booking']],
  }
  for (const [status, label] of transitions[item.status] ?? []) {
    const button = text('button', label)
    button.type = 'button'
    button.addEventListener('click', async () => {
      if (status === 'booked' && !confirm('Has the customer accepted this quote?')) return
      if (status === 'cancelled' && !confirm('Cancel this catering request?')) return
      for (const action of actions.children) action.disabled = true
      try {
        await request(path + '/status', 'PUT', { status })
        await refresh()
      } catch (error) {
        bookingStatus.textContent = error.message
      } finally {
        for (const action of actions.children) action.disabled = false
      }
    })
    actions.append(button)
  }
  row.append(actions)
  return row
}

async function refresh() {
  try {
    const items = await request('catering')
    list.replaceChildren(...items.map(renderBooking))
    bookingStatus.textContent = items.length ? '' : 'No inquiries yet.'
  } catch (error) {
    bookingStatus.textContent = error.message
  }
}

function paymentPath() {
  const data = paymentForm.elements
  return 'payments/' + data.namedItem('target').value + '/' +
    encodeURIComponent(data.namedItem('reference').value.trim())
}

async function showPayments(path) {
  const payments = await request(path)
  paymentList.replaceChildren(...payments.map(payment => text('li',
    payment.channel.toUpperCase() + ' · ' + payment.transaction_reference + ' · ' + money.format(payment.amount_ngwee / 100))))
  paymentStatus.textContent = payments.length ? '' : 'No payments recorded for this reference.'
}

document.querySelector('#lookup-payments').addEventListener('click', async () => {
  if (!paymentForm.elements.namedItem('reference').reportValidity()) return
  try { await showPayments(paymentPath()) } catch (error) { paymentStatus.textContent = error.message }
})
paymentForm.addEventListener('submit', async event => {
  event.preventDefault()
  const button = paymentForm.querySelector('button[type=submit]')
  button.disabled = true
  const data = new FormData(paymentForm)
  const path = paymentPath()
  try {
    await request(path, 'POST', {
      channel: data.get('channel'),
      transaction_reference: data.get('transaction_reference'),
      amount_ngwee: Math.round(Number(data.get('amount')) * 100),
      verified: data.has('verified'),
    })
    paymentForm.elements.namedItem('verified').checked = false
    try {
      await showPayments(path)
      paymentStatus.textContent = 'Payment recorded.'
    } catch {
      paymentStatus.textContent = 'Payment recorded. Use View recorded payments to refresh.'
    }
    await refresh()
  } catch (error) {
    paymentStatus.textContent = error.message
  } finally {
    button.disabled = false
  }
})
document.querySelector('#refresh-bookings').addEventListener('click', refresh)
refresh()
