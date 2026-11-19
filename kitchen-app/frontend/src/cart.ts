import { defineStore } from 'pinia'

type Item = { id: number; name: string; option: string; price_ngwee: number }
type Line = Item & { quantity: number }

export const useCart = defineStore('cart', {
  state: () => ({ lines: [] as Line[], submitting: false }),
  getters: {
    total: state => state.lines.reduce((sum, line) => sum + line.price_ngwee * line.quantity, 0),
    count: state => state.lines.reduce((sum, line) => sum + line.quantity, 0),
  },
  actions: {
    add(item: Item) {
      if (this.submitting) return
      const current = this.lines.find(line => line.id === item.id)
      if (current) {
        Object.assign(current, item, { quantity: Math.min(20, current.quantity + 1) })
      } else if (this.lines.length < 30) {
        this.lines.push({ id: item.id, name: item.name, option: item.option,
          price_ngwee: item.price_ngwee, quantity: 1 })
      }
    },
    adjust(id: number, difference: number) {
      const index = this.lines.findIndex(line => line.id === id)
      const line = this.lines[index]
      if (!line) return
      const quantity = line.quantity + difference
      if (quantity < 1) this.lines.splice(index, 1)
      else line.quantity = Math.min(20, quantity)
    },
  },
})

const formatter = new Intl.NumberFormat('en-ZM', { maximumFractionDigits: 2 })
export const money = (ngwee: number) => 'K' + formatter.format(ngwee / 100)

export function orderHistory(): string[] {
  try {
    const saved: unknown = JSON.parse(localStorage.getItem('percy-orders') ?? '[]')
    return Array.isArray(saved) ? saved.filter(id => typeof id === 'string') : []
  } catch {
    return []
  }
}

export function rememberOrder(reference: string) {
  try {
    localStorage.setItem('percy-orders', JSON.stringify([reference, ...orderHistory().filter(id => id !== reference)].slice(0, 20)))
  } catch {
    // The confirmation link remains available when browser storage is disabled.
  }
}
