import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'
import { VitePWA } from 'vite-plugin-pwa'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.ico', 'logo-kompas.png', 'apple-touch-icon-180x180.png'],
      manifest: {
        name: 'Kompás · Panel de administración',
        short_name: 'Kompás',
        description: 'Panel de administración de Kompás: estadísticas de uso y del sistema experto',
        lang: 'es-MX',
        start_url: '/',
        scope: '/',
        display: 'standalone',
        orientation: 'portrait',
        theme_color: '#1A62A5',
        background_color: '#f8fafc',
        icons: [
          { src: 'pwa-192x192.png', sizes: '192x192', type: 'image/png' },
          { src: 'pwa-512x512.png', sizes: '512x512', type: 'image/png' },
          { src: 'maskable-icon-512x512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' },
        ],
      },
      workbox: {
        // Los mosaicos del mapa y la API no se guardan en caché: siempre deben ser datos frescos
        navigateFallbackDenylist: [/^\/api\//],
      },
    }),
  ],
})
