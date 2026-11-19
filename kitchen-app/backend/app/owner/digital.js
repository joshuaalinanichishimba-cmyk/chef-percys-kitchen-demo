const editor = document.querySelector('#digital-product')
const list = document.querySelector('#digital-items')
const message = document.querySelector('#digital-status')
const sale = document.querySelector('#digital-sale')
const saleMessage = document.querySelector('#digital-sale-status')
const codeLabel = document.querySelector('#digital-code-label')
const code = document.querySelector('#digital-code')
const catalogue = sale.elements.namedItem('product')
const money = new Intl.NumberFormat('en-ZM', { style: 'currency', currency: 'ZMW' })
let editId = null
let saleAttempt = null

async function request(path, method = 'GET', data, upload = false) {
  const response = await fetch('/owner/api/digital' + path, {
    method,
    headers: { 'Content-Type': upload ? 'application/pdf' : 'application/json', 'X-Owner-Action': 'menu-edit' },
    body: upload ? data : data === undefined ? undefined : JSON.stringify(data),
  })
  if (response.status === 204) return null
  const result = await response.json()
  if (!response.ok) throw new Error(typeof result.detail === 'string' ? result.detail : 'Check the details and try again.')
  return result
}

function button(label, action) {
  const control = document.createElement('button')
  control.type = 'button'
  control.textContent = label
  control.addEventListener('click', async () => {
    control.disabled = true
    try {
      await action()
    } catch (error) {
      message.textContent = error.message
    } finally {
      control.disabled = false
    }
  })
  return control
}

function edit(item) {
  editId = item.id
  for (const name of ['title', 'description', 'kind']) editor.elements.namedItem(name).value = item[name]
  editor.elements.namedItem('price').value = item.price_ngwee / 100
  editor.querySelector('[type=submit]').textContent = 'Save changes'
  editor.elements.namedItem('title').focus()
}

function productRow(item) {
  const row = document.createElement('li')
  const name = document.createElement('strong')
  name.textContent = item.title + ' · ' + money.format(item.price_ngwee / 100)
  const state = document.createElement('p')
  state.textContent = (item.published ? 'Published' : 'Draft') + (item.has_pdf ? ' · PDF uploaded' : ' · PDF needed')
  const actions = document.createElement('div')
  actions.className = 'order-actions'
  actions.append(button('Edit details', () => edit(item)))
  if (!item.published) {
    const upload = document.createElement('input')
    upload.type = 'file'
    upload.accept = '.pdf,application/pdf'
    upload.setAttribute('aria-label', 'PDF for ' + item.title)
    actions.append(upload, button('Upload PDF', async () => {
      const file = upload.files[0]
      if (!file || file.size > 10 * 1024 * 1024) throw new Error('Choose a PDF up to 10 MB.')
      await request('/' + item.id + '/pdf', 'PUT', file, true)
      await refresh()
      message.textContent = 'PDF saved.'
    }))
  }
  if (item.has_pdf) {
    actions.append(button(item.published ? 'Hide product' : 'Publish product', async () => {
      await request('/' + item.id + '/publication', 'PUT', { published: !item.published })
      await refresh()
    }))
  }
  row.append(name, state, actions)
  return row
}

async function refresh() {
  const items = await request('')
  const selected = catalogue.value
  catalogue.replaceChildren(new Option('Select a product', ''), ...items.map(item => new Option(item.title + ' · ' + money.format(item.price_ngwee / 100) +
      (item.published ? '' : ' · Hidden'), String(item.id))))
  catalogue.value = Array.from(catalogue.options).some(option => option.value === selected) ? selected : ''
  list.replaceChildren(...items.map(productRow))
  message.textContent = items.length ? '' : 'No products yet.'
}

editor.addEventListener('reset', () => {
  editId = null
  editor.querySelector('[type=submit]').textContent = 'Save draft'
})
editor.addEventListener('submit', async event => {
  event.preventDefault()
  const submit = editor.querySelector('[type=submit]')
  submit.disabled = true
  const form = new FormData(editor)
  try {
    await request(editId === null ? '' : '/' + editId, editId === null ? 'POST' : 'PUT', {
      title: form.get('title'), description: form.get('description'), kind: form.get('kind'),
      price_ngwee: Math.round(Number(form.get('price')) * 100),
    })
    editor.reset()
    await refresh()
    message.textContent = 'Product saved.'
  } catch (error) {
    message.textContent = error.message
  } finally {
    submit.disabled = false
  }
})

sale.addEventListener('submit', async event => {
  event.preventDefault()
  const replace = event.submitter?.value === 'replace'
  if (replace && !confirm('Replace the code for this sale? The old code will stop working.')) return
  const buttons = sale.querySelectorAll('[type=submit]')
  for (const button of buttons) button.disabled = true
  const fields = new FormData(sale)
  const path = '/' + fields.get('product') + '/sales'
  const payment = {
    channel: fields.get('channel'), transaction_reference: fields.get('transaction_reference'),
    amount_ngwee: Math.round(Number(fields.get('amount')) * 100), verified: fields.has('verified'),
    replace_code: replace,
  }
  const key = path + JSON.stringify(payment)
  if (saleAttempt?.key !== key) {
    const token = Array.from(crypto.getRandomValues(new Uint8Array(32)), byte => byte.toString(16).padStart(2, '0')).join('')
    saleAttempt = { key, token }
  }
  const sentToken = saleAttempt.token
  try {
    const result = await request(path, 'POST', { ...payment, token: sentToken })
    if (replace) saleAttempt = null
    code.value = sentToken
    codeLabel.hidden = false
    code.select()
    saleMessage.textContent = 'Sale ' + result.reference + ' recorded. Share this code privately. It expires in seven days.'
  } catch (error) {
    saleMessage.textContent = error.message
  } finally {
    for (const button of buttons) button.disabled = false
  }
})
refresh().catch(error => { message.textContent = error.message })
