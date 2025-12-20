import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    allowedHosts: [
      'overflowing-purpose-production-2b8e.up.railway.app',
      'localhost'
    ]
  }
})
