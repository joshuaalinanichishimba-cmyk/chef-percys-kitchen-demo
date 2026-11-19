import { defineStore } from 'pinia'

export const location = 'L237, CBU Campus, Kitwe'
export const contacts = [
  { network: 'Airtel', number: '0779079908', international: '+260779079908' },
  { network: 'MTN', number: '0760892063', international: '+260760892063' },
]
export function whatsapp(message: string) {
  return 'https://wa.me/260779079908?text=' + encodeURIComponent(message)
}

export const photos = [
  { name: 'Shawarma & fries', image: 'shawarma', category: 'Meals', alt: 'Loaded shawarma and fries in a takeaway tray' },
  { name: 'From the grill', image: 'grill', category: 'Grill', alt: 'Glazed grilled meat served in a round pan' },
  { name: 'Seafood', image: 'seafood', category: 'Meals', alt: 'Mussels with vegetables in a white bowl' },
  { name: 'Pasta', image: 'pasta', category: 'Meals', alt: 'Pasta tossed with vegetables in a dark bowl' },
  { name: 'Braai', image: 'braai', category: 'Grill', alt: 'Sausages and meat cooking over coals' },
  { name: 'A table for sharing', image: 'spread', category: 'Events', alt: 'Several shared dishes and sides arranged on a table' },
  { name: 'Platters & sides', image: 'platters', category: 'Events', alt: 'Grilled meat with rice and mixed salad' },
  { name: 'Noodles', image: 'noodles', category: 'Meals', alt: 'A pan of noodles prepared by Chef Percy' },
  { name: 'Event drinks', image: 'drinks', category: 'Events', alt: 'Four drinks lined up at an event' },
  { name: 'Fresh sides', image: 'salad', category: 'Meals', alt: 'Colourful mixed salad on a white plate' },
]
export const filters = ['All', 'Meals', 'Grill', 'Events']
export const useGallery = defineStore('gallery', {
  state: () => ({ filter: 'All' }),
  getters: {
    visible: state => state.filter === 'All' ? photos : photos.filter(photo => photo.category === state.filter),
  },
})
