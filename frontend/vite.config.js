import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [tailwindcss(), react()],
  server: {
    proxy: {
      '/query': 'http://localhost:8000',
      '/health': 'http://localhost:8000',
      '/stats': 'http://localhost:8000',
    },
  },
})
