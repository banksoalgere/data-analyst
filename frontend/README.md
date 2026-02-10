# Frontend

Next.js App Router frontend for dataset upload, preview, and chat-driven analysis.

## Run

```bash
npm install
npm run dev -- --hostname 127.0.0.1 --port 3000
```

Open:
- [http://127.0.0.1:3000/dashboard](http://127.0.0.1:3000/dashboard)

## Notes

- API calls are proxied through `app/api/*`.
- Analysis requests use streaming via `POST /api/analyze/stream`.
- SSE parsing and progress formatting are centralized in `lib/analyze-stream.ts`.

## Lint

```bash
npm run lint
```

See the project root `README.md` for full architecture and backend integration details.
