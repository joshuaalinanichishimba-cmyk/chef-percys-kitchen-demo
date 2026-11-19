<script setup lang="ts">
import { contacts, filters, location, photos, useGallery, whatsapp } from './kitchen'
defineProps<{ page: string }>()
const gallery = useGallery()
const preorder = whatsapp('Hi Chef Percy, I’d like to ask about a pre-order. What’s available?')
const catering = whatsapp('Hi Chef Percy, I’d like to enquire about catering for an event.')
</script>

<template>
  <main v-if="page === 'home'" tabindex="-1">
    <section class="hero">
      <div class="wrap hero-inner">
        <div class="hero-copy">
          <p class="eyebrow"><span></span> CBU CAMPUS · KITWE</p>
          <h1>Platters that<br><em>matter.</em></h1>
          <p class="hero-text">Shawarma platters, wings and braai spreads, made fresh to order by Chef Percy Chanda.</p>
          <div class="actions">
            <a class="button" :href="preorder">Pre-order on WhatsApp</a>
            <RouterLink class="button outline" to="/menu">View the menu</RouterLink>
          </div>
        </div>
      </div>
      <img class="hero-photo" src="/images/platters.webp" alt="Chef Percy’s spread of grilled meat, rice and salad" fetchpriority="high">
    </section>

    <div class="service-bar">
      <div class="wrap service-inner">
        <span><i aria-hidden="true"></i> Made fresh to order</span>
        <span><i aria-hidden="true"></i> Pickup at L237, CBU</span>
        <span><i aria-hidden="true"></i> Delivery via Yango</span>
      </div>
    </div>

    <section class="wrap section">
      <div class="section-heading">
        <div><p class="eyebrow">FROM THE KITCHEN</p><h2>What’s cooking</h2></div>
        <RouterLink class="text-link" to="/food">See all food photos</RouterLink>
      </div>
      <div class="photo-grid">
        <figure v-for="photo in photos.slice(0,3)" :key="photo.image" class="food-card">
          <img :src="'/images/' + photo.image + '.webp'" :alt="photo.alt" loading="lazy">
          <figcaption>{{ photo.name }}</figcaption>
        </figure>
      </div>
    </section>

    <section class="dark-section">
      <div class="wrap feature">
        <img src="/images/spread.webp" alt="Shared dishes from Percy’s kitchen set out on a table" loading="lazy">
        <div><p class="eyebrow">CATERING & EVENTS</p><h2>Bring everyone to the table.</h2>
          <p>Plan a braai, a seafood boil or a catered spread for your next gathering in Kitwe.</p>
          <RouterLink class="button" to="/catering">Explore catering</RouterLink>
        </div>
      </div>
    </section>

    <section class="wrap section feature chef-feature">
      <img src="/images/chef.webp" alt="Chef Percy Chanda in his apron" loading="lazy">
      <div><p class="eyebrow">THE CHEF</p><h2>Meet Percy Chanda.</h2>
        <p>Known as “The Best Chef in CBU,” Percy cooks for students, staff and the wider Kitwe community from his kitchen at L237.</p>
        <RouterLink class="text-link" to="/about">About Percy’s kitchen</RouterLink>
      </div>
    </section>
  </main>

  <main v-else-if="page === 'food'" class="wrap section inside" tabindex="-1">
    <p class="eyebrow">FROM THE KITCHEN</p><h1>Our food</h1>
    <p>Explore Percy’s food photography and ask what’s available for your next pre-order.</p>
    <div class="filters" role="group" aria-label="Filter food photographs">
      <button v-for="filter in filters" :key="filter" type="button" :aria-pressed="gallery.filter === filter" @click="gallery.filter = filter">{{ filter }}</button>
    </div>
    <div class="photo-grid">
      <figure v-for="photo in gallery.visible" :key="photo.image" class="food-card">
        <img :src="'/images/' + photo.image + '.webp'" :alt="photo.alt" loading="lazy">
        <figcaption>{{ photo.name }}</figcaption>
      </figure>
    </div>
    <a class="button after-grid" :href="preorder">Ask about availability</a>
  </main>

  <main v-else-if="page === 'catering'" class="wrap section inside" tabindex="-1">
    <div class="feature">
      <div><p class="eyebrow">CATERING & EVENTS</p><h1>Food for a crowd</h1>
        <p>From a seafood boil to a full braai spread, Percy prepares food for gatherings and events in Kitwe.</p>
        <ul class="service-list"><li>Event catering</li><li>Braai packages</li><li>Seafood boils</li></ul>
        <p>Share your event date, guest count and venue when you get in touch.</p>
        <a class="button" :href="catering">Enquire on WhatsApp</a>
      </div>
      <img src="/images/spread.webp" alt="A variety of dishes from Chef Percy’s kitchen arranged for sharing">
    </div>
  </main>

  <main v-else-if="page === 'about'" class="wrap section inside" tabindex="-1">
    <div class="feature chef-feature">
      <img src="/images/chef.webp" alt="Chef Percy Chanda in his apron">
      <div><p class="eyebrow">THE CHEF</p><h1>Meet Percy Chanda</h1>
        <p>Known as “The Best Chef in CBU,” Percy cooks fresh-to-order meals at L237, CBU Campus, Kitwe.</p>
        <p>His kitchen serves students, staff and the wider community through daily pre-orders, catering and event services.</p>
        <RouterLink class="button" to="/contact">Contact the kitchen</RouterLink>
      </div>
    </div>
  </main>

  <main v-else class="wrap section inside" tabindex="-1">
    <p class="eyebrow">CBU CAMPUS · KITWE</p><h1>Contact the kitchen</h1>
    <div class="contact-grid">
      <section><h2>Talk to Percy</h2><p>Message Percy to ask about availability, place a pre-order or plan an event.</p>
        <a class="button" :href="preorder">Message on WhatsApp</a>
        <ul class="service-list"><li v-for="contact in contacts" :key="contact.network">{{ contact.network }} · <a class="text-link" :href="'tel:' + contact.international">{{ contact.number }}</a></li></ul>
      </section>
      <section><h2>Pickup & delivery</h2><p>Collect your pre-order at {{ location }}.</p><p>Ask Percy to confirm your pickup time or arrange delivery via Yango.</p></section>
    </div>
  </main>
</template>
