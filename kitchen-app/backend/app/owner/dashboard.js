const list = document.querySelector('#entries')
const form = document.querySelector('#editor')
const status = document.querySelector('#status')
const fields = form.elements
const submit = form.querySelector('button[type=submit]')
let selected = null

async function request(path, options) {
  const response = await fetch('/owner/api/menu' + path, options)
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    const message = Array.isArray(body.detail)
      ? body.detail.map(error => error.msg).join(' ')
      : body.detail
    throw new Error(message || 'Request failed (' + response.status + ').')
  }
  return response.json()
}

function openEditor(entry = null) {
  selected = entry?.id ?? null
  form.reset()
  document.querySelector('#form-title').textContent = entry ? 'Edit menu entry' : 'New entry'
  if (entry) {
    for (const name of ['name', 'category', 'option', 'description']) fields.namedItem(name).value = entry[name]
    fields.price_ngwee.value = entry.price_ngwee / 100
    fields.max_price_ngwee.value = entry.max_price_ngwee === null ? '' : entry.max_price_ngwee / 100
    fields.available.checked = entry.available
    fields.starting_at.checked = entry.starting_at
  }
  form.hidden = false
  fields.category.focus()
}

async function refresh() {
  const entries = await request('')
  list.replaceChildren(...entries.map(entry => {
    const row = document.createElement('li')
    const button = document.createElement('button')
    button.type = 'button'
    button.textContent = [entry.category, entry.name, entry.option, entry.available ? '' : 'Hidden']
      .filter(Boolean).join(' · ')
    button.addEventListener('click', () => openEditor(entry))
    row.append(button)
    return row
  }))
}

document.querySelector('#new-entry').addEventListener('click', () => openEditor())
form.addEventListener('submit', async event => {
  event.preventDefault()
  submit.disabled = true
  status.textContent = 'Saving menu entry…'
  const data = Object.fromEntries(new FormData(form))
  data.price_ngwee = Math.round(Number(data.price_ngwee) * 100)
  data.max_price_ngwee = data.max_price_ngwee === '' ? null : Math.round(Number(data.max_price_ngwee) * 100)
  data.available = fields.available.checked
  data.starting_at = fields.starting_at.checked
  try {
    const entry = await request(selected === null ? '' : '/' + selected, {
      method: selected === null ? 'POST' : 'PUT',
      headers: { 'Content-Type': 'application/json', 'X-Owner-Action': 'menu-edit' },
      body: JSON.stringify(data),
    })
    selected = entry.id
    document.querySelector('#form-title').textContent = 'Edit menu entry'
    status.textContent = 'Saved.'
    try {
      await refresh()
    } catch {
      status.textContent = 'Saved. Reload to refresh the entry list.'
    }
  } catch (error) {
    status.textContent = error.message
  } finally {
    submit.disabled = false
  }
})
refresh().catch(error => { status.textContent = error.message })

const orderStatus = document.querySelector('#orders-status')
const orderList = document.querySelector('#orders')
const refreshOrdersButton = document.querySelector('#refresh-orders')
const currency = new Intl.NumberFormat('en-ZM', { style: 'currency', currency: 'ZMW' })

const nextStatus = {
  received: [['confirmed', 'Confirm'], ['cancelled', 'Cancel']],
  confirmed: [['preparing', 'Start preparing'], ['cancelled', 'Cancel']],
  preparing: [['ready', 'Mark ready'], ['cancelled', 'Cancel']],
  ready: [['completed', 'Complete'], ['cancelled', 'Cancel']],
}

async function changeOrderStatus(order, target, actions) {
  if (target === 'cancelled' && !confirm('Cancel this order request?')) return
  for (const button of actions.children) button.disabled = true
  try {
    const response = await fetch('/owner/api/orders/' + encodeURIComponent(order.reference) + '/status', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', 'X-Owner-Action': 'menu-edit' },
      body: JSON.stringify({ status: target }),
    })
    if (!response.ok) throw new Error('Could not change status. Refresh the order list and try again.')
    await refreshOrders()
  } catch (error) {
    orderStatus.textContent = error.message
  } finally {
    for (const button of actions.children) button.disabled = false
  }
}

async function refreshOrders() {
  refreshOrdersButton.disabled = true
  orderStatus.textContent = 'Loading order requests…'
  try {
    const response = await fetch('/owner/api/orders')
    if (!response.ok) throw new Error('Could not load orders (' + response.status + ').')
    const orders = await response.json()
    orderList.replaceChildren(...orders.map(order => {
      const row = document.createElement('li')
      const heading = document.createElement('strong')
      heading.textContent = order.customer_name + ' · ' + order.phone
      const summary = document.createElement('p')
      summary.textContent = [
        new Date(order.created_at).toLocaleString('en-ZM', { timeZone: 'Africa/Johannesburg' }),
        order.fulfillment === 'pickup' ? 'Pickup' : 'Yango · ' + order.address,
        currency.format(order.total_ngwee / 100) + ' food subtotal',
        currency.format(order.paid_ngwee / 100) + ' recorded paid',
      ].join(' · ')
      const items = document.createElement('p')
      items.textContent = order.items.map(line => line.quantity + ' × ' + line.name + ' ' + line.option).join(', ')
      const reference = document.createElement('small')
      reference.textContent = order.reference
      const state = document.createElement('p')
      state.textContent = 'Status: ' + order.status
      const actions = document.createElement('div')
      actions.className = 'order-actions'
      for (const [target, label] of nextStatus[order.status] ?? []) {
        const button = document.createElement('button')
        button.type = 'button'
        button.textContent = label
        button.addEventListener('click', () => changeOrderStatus(order, target, actions))
        actions.append(button)
      }
      row.append(heading, summary, items, reference, state, actions)
      return row
    }))
    orderStatus.textContent = orders.length ? '' : 'No order requests yet.'
  } catch (error) {
    orderStatus.textContent = error.message
  } finally {
    refreshOrdersButton.disabled = false
  }
}

refreshOrdersButton.addEventListener('click', refreshOrders)
refreshOrders()

const capacity = document.querySelector('#capacity')
const capacityInput = capacity.elements.namedItem('daily_limit')
const capacityStatus = document.querySelector('#capacity-status')
const capacitySubmit = capacity.querySelector('button')

async function updateCapacity(options) {
  capacitySubmit.disabled = true
  try {
    const response = await fetch('/owner/api/capacity', options)
    if (!response.ok) throw new Error('Could not load or save the order limit.')
    const data = await response.json()
    capacityInput.value = data.daily_limit ?? ''
    capacityStatus.textContent = data.requests_today + ' requests today. ' +
      (data.daily_limit === null ? 'No daily limit.' : 'Daily limit: ' + data.daily_limit + '.')
  } catch (error) {
    capacityStatus.textContent = error.message
  } finally {
    capacitySubmit.disabled = false
  }
}

capacity.addEventListener('submit', event => {
  event.preventDefault()
  updateCapacity({
    method: 'PUT',
    headers: { 'Content-Type': 'application/json', 'X-Owner-Action': 'menu-edit' },
    body: JSON.stringify({ daily_limit: capacityInput.value === '' ? null : capacityInput.valueAsNumber }),
  })
})
updateCapacity()
