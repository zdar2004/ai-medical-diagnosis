# MediSysAI CDS — Frontend Foundation

Frontend foundation for an **AI-Powered Medical Diagnosis & Clinical Decision
Support System**. This is the project scaffold only — no API integration yet.
It is built to later connect to an existing FastAPI backend.

## Stack

- React 19
- Vite
- JavaScript (no TypeScript)
- React Router DOM (`createBrowserRouter`)
- Axios (installed, not yet wired to any endpoint)
- CSS Modules (no Tailwind / Bootstrap)

## Getting started

```bash
npm install
npm run dev
```

The app runs at `http://localhost:5173`.

## Project structure

```
src/
  components/   # Shared, reusable UI components (empty — none yet)
  layouts/      # Page shells, e.g. MainLayout (header/nav/footer)
  pages/        # Route-level pages (Home, Login, NotFound)
  services/     # Future API clients (axios instances, endpoints)
  hooks/        # Shared custom hooks
  assets/       # Static assets (images, icons)
  styles/       # Global CSS and design tokens (variables.css, global.css)
  utils/        # Shared helper functions
  routes/       # Router configuration (AppRouter.jsx)
```

## Current routes

| Path      | Page     |
| --------- | -------- |
| `/`       | Home     |
| `/login`  | Login    |
| `*`       | NotFound |

`Dashboard`, `Patients`, and `Diagnosis` routes are intentionally **not**
implemented yet — they will be added once the backend integration begins.

## Notes

- No API calls are implemented. `axios` is installed and ready for a future
  `services/` layer once backend endpoints are available.
- The Login page renders a controlled form only; submission is a no-op
  (`event.preventDefault()`) until the auth API is connected.
- Design tokens (color, type, spacing) live in `src/styles/variables.css`
  and are consumed via CSS Modules across the app.
