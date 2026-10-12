import fs from 'node:fs'
import path from 'node:path'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// GitHub Pages answers /chaoss/ with chaoss/index.html; the dev server answers every unknown path
// with the app instead, so the static pages in public/ (the CHAOSS methodology page, the API guide,
// the privacy notice) opened blank locally. Serve them the way Pages does.
const publicIndexPages = () => ({
  name: 'public-index-pages',
  configureServer(server) {
    const root = path.resolve(server.config.publicDir)
    server.middlewares.use((req, _res, next) => {
      const [pathname, query] = req.url.split('?')
      if (pathname.length > 1 && pathname.endsWith('/')) {
        let decoded
        try {
          decoded = decodeURIComponent(pathname)
        } catch {
          return next() // a malformed escape is not one of our pages; let Vite answer it
        }
        const file = path.join(root, decoded, 'index.html')
        if (file.startsWith(root + path.sep) && fs.existsSync(file)) {
          req.url = `${pathname}index.html${query ? `?${query}` : ''}`
        }
      }
      next()
    })
  },
})

export default defineConfig({
  plugins: [react(), publicIndexPages()],
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

