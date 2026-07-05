# UI Migration Guide: HTMX to React / Next.js

This guide outlines the architectural shift and practical steps required to migrate the frontend of your ERP framework from Server-Side Rendered (SSR) Django HTMX templates to a fully decoupled Single Page Application (SPA) using React or Next.js.

*(Note: This assumes you have already implemented the Headless API via Django REST Framework as outlined in the DRF Migration Guide).*

---

## 1. Architectural Paradigm Shift

When migrating from HTMX to React, the fundamental mental model changes:
*   **HTMX / Django:** The server holds the state. The server sends HTML fragments. The browser just swaps them in.
*   **React / Next.js:** The browser holds the state. The server sends raw JSON data. The browser builds the HTML locally.

## 2. Infrastructure & Setup

To fully decouple, your frontend will run on an entirely separate server (a Node.js server) from your backend (Django/Python).

### Next.js Initialization
We highly recommend **Next.js** over standard React, as it provides SSR capabilities, built-in routing, and SEO optimization.
```bash
# Run this in a directory outside of your Django project
npx create-next-app@latest erp-frontend
# Select 'Yes' for Tailwind CSS and App Router during setup
```

### Docker Integration
You will need to update your `docker-compose.yml` to include the new frontend service alongside your Django `web` service.
```yaml
  frontend:
    build: ./erp-frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

---

## 3. Translating Components

Because your Django templates already use **Tailwind CSS**, migrating the styling is practically a 1:1 copy/paste. However, the component structure changes.

### Django Template Example
```html
<!-- Django: core/components/dashboard/stat_card.html -->
<div class="bg-white rounded-xl p-6">
    <h3>{{ title }}</h3>
    <p>{{ value }}</p>
</div>
```

### React Component Equivalent
You will translate Django `context` variables into React `props`.
```tsx
// React: src/components/dashboard/StatCard.tsx
interface StatCardProps {
    title: string;
    value: string | number;
}

export default function StatCard({ title, value }: StatCardProps) {
    return (
        <div className="bg-white rounded-xl p-6">
            <h3>{title}</h3>
            <p>{value}</p>
        </div>
    );
}
```

---

## 4. State Management & Data Fetching

HTMX automatically handled data fetching via attributes like `hx-get`. In React, you must manually fetch JSON and store it in state.

### Using React Query or SWR (Recommended)
Instead of standard `useEffect` hooks, use a library like SWR or TanStack Query to manage loading states, caching, and background fetching—mimicking the ease of HTMX.

```tsx
import useSWR from 'swr';
import StatCard from '@/components/dashboard/StatCard';

const fetcher = (url: string) => fetch(url, {
    headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` }
}).then(res => res.json());

export default function Dashboard() {
    const { data, error, isLoading } = useSWR(
        `${process.env.NEXT_PUBLIC_API_URL}/pos/stats/`, 
        fetcher
    );

    if (isLoading) return <div>Loading real-time analytics...</div>;
    if (error) return <div>Failed to load data.</div>;

    return (
        <StatCard title="Total Purchase Orders" value={data.total_pos} />
    );
}
```

---

## 5. Handling Authentication (JWT)

Django natively handled authentication securely via HTTP-Only Session Cookies. In a decoupled React app, you will rely on **JWT (JSON Web Tokens)**.

### The Authentication Flow
1. **Login:** The React app sends a POST request with `username` and `password` to Django's `/api/v1/auth/token/`.
2. **Storage:** Django returns an `access_token` (valid for 15 minutes) and a `refresh_token` (valid for 7 days). Store the `access_token` in memory or `localStorage`, and securely store the `refresh_token` (preferably in an HTTP-only cookie).
3. **Usage:** For every subsequent API request (like fetching Inventory Items), React must attach the token to the header:
   `Authorization: Bearer <access_token>`
4. **Interceptors:** Use an HTTP client like `axios` to create an "interceptor". If a request fails with a 401 (Unauthorized) because the token expired, the interceptor automatically sends the `refresh_token` to get a new `access_token` and retries the original request seamlessly.

---

## 6. Routing Translation

Django's `urls.py` mapped URLs directly to Views. Next.js uses **File-Based Routing**.

| Django URL Route | Next.js File Path | Purpose |
| :--- | :--- | :--- |
| `path('dashboard/', views.dashboard)` | `app/dashboard/page.tsx` | Main dashboard view |
| `path('po/', views.po_list)` | `app/po/page.tsx` | Table list of all orders |
| `path('po/<int:pk>/', views.po_detail)` | `app/po/[id]/page.tsx` | Detail view for a specific order |

## 7. Migration Strategy Checklist

1. [ ] **Build API:** Finalize the DRF API endpoints (as per the DRF Migration Guide).
2. [ ] **Setup CORS:** Install `django-cors-headers` in Django and allow `http://localhost:3000` so React can talk to Django.
3. [ ] **Initialize Next.js:** Scaffold the new frontend repository.
4. [ ] **Component Porting:** Port all atomic UI components (Buttons, Inputs, Modals) from Django `{% include %}` to React `.tsx` files. Tailwind makes this fast.
5. [ ] **Auth Layer:** Implement the JWT Login form and Axios interceptors.
6. [ ] **Page Assembly:** Begin rebuilding the actual pages (Dashboard, PO List, Details) utilizing the React components and pulling data from the API.
7. [ ] **Decommission HTMX:** Once the React app reaches parity, you can safely remove the `templates/` folder from Django, completing the decoupling.
