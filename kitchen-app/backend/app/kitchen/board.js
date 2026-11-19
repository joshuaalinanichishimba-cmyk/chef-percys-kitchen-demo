const board = document.querySelector('#board')
const status = document.querySelector('#status')
const columns = { confirmed: 'To prepare', preparing: 'Preparing', ready: 'Ready' }
const next = { confirmed: ['preparing', 'Start preparing'], preparing: ['ready', 'Mark ready'] }
let previous = ''
let busy = false

function ticket(order) {
  const card = document.createElement('article')
  const title = document.createElement('h3')
  title.textContent = (order.fulfillment === 'pickup' ? 'Pickup' : 'Delivery') + ' · ' + order.reference.slice(0, 8)
  const items = document.createElement('ul')
  for (const item of order.items) {
    const line = document.createElement('li')
    line.textContent = item.quantity + ' × ' + [item.name, item.option].filter(Boolean).join(' · ')
    items.append(line)
  }
  card.append(title, items)
  const action = next[order.status]
  if (action) {
    const button = document.createElement('button')
    button.type = 'button'
    button.textContent = action[1]
    button.addEventListener('click', async () => {
      if (busy) return
      busy = true
      button.disabled = true
      try {
        const response = await fetch('/kitchen/api/orders/' + encodeURIComponent(order.reference) + '/status', {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json', 'X-Owner-Action': 'menu-edit' },
          body: JSON.stringify({ status: action[0] }),
        })
        if (!response.ok) throw new Error('Could not update this ticket. The board will refresh.')
      } catch (error) {
        status.textContent = error.message
      } finally {
        button.disabled = false
        busy = false
      }
      await refresh()
    })
    card.append(button)
  }
  return card
}

async function refresh() {
  if (busy) return
  busy = true
  try {
    const response = await fetch('/kitchen/api/orders')
    if (!response.ok) throw new Error('Could not refresh the board. Check your kitchen login and connection.')
    const orders = await response.json()
    const snapshot = JSON.stringify(orders)
    if (snapshot !== previous) {
      board.replaceChildren(...Object.entries(columns).map(([key, label]) => {
        const section = document.createElement('section')
        const heading = document.createElement('h2')
        heading.textContent = label
        const tickets = orders.filter(order => order.status === key).map(ticket)
        if (tickets.length === 0) {
          const empty = document.createElement('p')
          empty.textContent = 'No tickets.'
          tickets.push(empty)
        }
        section.append(heading, ...tickets)
        return section
      }))
      previous = snapshot
    }
    status.textContent = ''
  } catch (error) {
    status.textContent = error.message
  } finally {
    busy = false
  }
}

await refresh()
setInterval(refresh, 5000)
