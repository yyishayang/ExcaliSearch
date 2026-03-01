// SPDX-FileCopyrightText: 2026 @albabsuarez
// SPDX-FileCopyrightText: 2026 @aslangallery
// SPDX-FileCopyrightText: 2026 @david598Uni
// SPDX-FileCopyrightText: 2026 @yyishayang
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react({
      babel: {
        plugins: [['babel-plugin-react-compiler']],
      },
    }),
  ],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
