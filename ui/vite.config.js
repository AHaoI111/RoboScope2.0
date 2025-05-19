import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '192.168.0.200',  // 设置为 0.0.0.0 允许通过局域网访问
    port: 5173,       // 设置端口
  }
})
