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
