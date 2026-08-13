# AIOS Dashboard (M3-P5)

React + Vite SPA — 10 views đọc hệ thống AIOS qua REST API + WebSocket.

## Chạy

```bash
# 1. Backend (từ backend/)
aiagent serve --port 8000

# 2. Dashboard (từ dashboard/)
npm install
npm run dev        # http://localhost:5173 (proxy /api → 127.0.0.1:8000, ws: true)
```

Production: `VITE_API_BASE=http://127.0.0.1:8000 npm run build` → `dist/`.

## Views

Chat · Workflow · Events (WS realtime) · Tools · Memory · Artifacts · Skills · Models · Prompts · Health

## Test

```bash
npm run test   # vitest (12 tests)
npm run build  # tsc + vite build
```
