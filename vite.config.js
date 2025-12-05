import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  base: './', // Use relative paths for GitHub Pages
  build: {
    outDir: 'docs',
    emptyOutDir: false, // Keep docs/data_catalog.xlsx and other generated assets between builds
    rollupOptions: {
      output: {
        // Ensure consistent file names for easier debugging
        entryFileNames: 'assets/[name].js',
        chunkFileNames: 'assets/[name].js',
        assetFileNames: 'assets/[name].[ext]'
      }
    }
  },
  server: {
    port: 3000,
    open: true
  },
  publicDir: 'public' // Static assets that get copied to docs/
})

