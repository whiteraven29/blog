# wh1t3r4v3n Blog — Full Documentation

A full-stack blog built for publishing offensive security writeups, CTF walkthroughs, web development guides, and programming articles. Dark monospace theme inspired by a developer portfolio design.

---

## Table of Contents

1. [Overview](#1-overview)
2. [Tech Stack](#2-tech-stack)
3. [Project Structure](#3-project-structure)
4. [Setup & Installation](#4-setup--installation)
5. [Backend Reference](#5-backend-reference)
   - [Database Models](#51-database-models)
   - [API Endpoints](#52-api-endpoints)
   - [Authentication](#53-authentication)
   - [Configuration](#54-configuration)
6. [Frontend Reference](#6-frontend-reference)
   - [Pages & Routes](#61-pages--routes)
   - [Components](#62-components)
   - [API Client](#63-api-client)
   - [Auth Context](#64-auth-context)
   - [Theme & Styling](#65-theme--styling)
7. [Writing Posts](#7-writing-posts)
   - [In-browser Editor](#71-in-browser-editor)
   - [Dashboard](#72-dashboard)
   - [Obsidian / Markdown Import](#73-obsidian--markdown-import)
8. [Deployment](#8-deployment)
9. [Environment & Seed Credentials](#9-environment--seed-credentials)

---

## 1. Overview

| Layer    | Technology                                  |
|----------|---------------------------------------------|
| Backend  | Django 4.2 + Django REST Framework          |
| Auth     | JWT via `djangorestframework-simplejwt`     |
| Database | SQLite (dev) — swappable to PostgreSQL      |
| Frontend | React 19 + Vite                             |
| Routing  | React Router v7                             |
| HTTP     | Axios with JWT refresh interceptor          |
| Editor   | `@uiw/react-md-editor` (live preview)       |
| Markdown | `react-markdown` + `remark-gfm` + `rehype-highlight` |
| Styling  | Plain CSS with custom properties, JetBrains Mono font |

The backend exposes a REST API at `/api/`. The frontend is a fully separate SPA that consumes it. In development both run independently; in production the frontend is compiled and served as static files.

---

## 2. Tech Stack

### Backend packages

| Package                          | Purpose                              |
|----------------------------------|--------------------------------------|
| `django`                         | Web framework                        |
| `djangorestframework`            | REST API layer                       |
| `djangorestframework-simplejwt`  | JWT access + refresh tokens          |
| `django-cors-headers`            | CORS for local frontend dev          |
| `django-filter`                  | Query filtering on list endpoints    |
| `Pillow`                         | Cover image and avatar uploads       |
| `PyYAML`                         | Frontmatter parsing in import command|

### Frontend packages

| Package                | Purpose                              |
|------------------------|--------------------------------------|
| `react-router-dom`     | Client-side routing                  |
| `axios`                | HTTP requests + interceptors         |
| `react-markdown`       | Markdown rendering in post detail    |
| `remark-gfm`           | Tables, task lists, strikethrough    |
| `rehype-highlight`     | Syntax highlighting in code blocks   |
| `highlight.js`         | Highlight.js styles (`github-dark`)  |
| `@uiw/react-md-editor` | Full markdown editor with preview    |
| `date-fns`             | Date formatting                      |

---

## 3. Project Structure

```
blog/
├── backend/
│   ├── config/                  # Django project config
│   │   ├── settings.py
│   │   ├── urls.py              # Root URL: /api/blog/ + /api/auth/
│   │   ├── wsgi.py
│   │   └── asgi.py
│   ├── blog/                    # Main blog app
│   │   ├── models.py            # Post, Category, Tag, Comment, Newsletter
│   │   ├── serializers.py       # DRF serializers
│   │   ├── views.py             # All API views
│   │   ├── urls.py              # Blog URL patterns
│   │   ├── admin.py             # Django admin config
│   │   └── management/
│   │       └── commands/
│   │           └── import_post.py   # CLI: import .md files
│   ├── accounts/                # Auth + user profile app
│   │   ├── models.py            # Profile (extends User)
│   │   ├── serializers.py
│   │   ├── views.py             # Login, profile, me
│   │   └── urls.py
│   ├── media/                   # Uploaded covers & avatars (gitignored)
│   ├── db.sqlite3               # SQLite database
│   ├── seed_posts.py            # One-time seed script
│   └── manage.py
│
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   │   └── client.js        # Axios instance + all API methods
│   │   ├── context/
│   │   │   └── AuthContext.jsx  # Global auth state (user, login, logout)
│   │   ├── components/
│   │   │   ├── Navbar.jsx / .css
│   │   │   ├── Footer.jsx / .css
│   │   │   ├── PostCard.jsx / .css   # Card used in grids
│   │   │   ├── ProtectedRoute.jsx    # Redirect to /login if unauthenticated
│   │   │   └── Spinner.jsx / .css
│   │   ├── pages/
│   │   │   ├── Home.jsx / .css        # Hero, stats, featured, categories, newsletter
│   │   │   ├── PostList.jsx / .css    # Filterable post grid
│   │   │   ├── PostDetail.jsx / .css  # Full post + comments
│   │   │   ├── Categories.jsx / .css  # Category browser
│   │   │   ├── CategoryDetail.jsx     # Posts filtered by category
│   │   │   ├── About.jsx / .css       # About page with terminal widget
│   │   │   ├── Contact.jsx / .css     # Contact form
│   │   │   ├── Login.jsx / .css       # Login form
│   │   │   ├── Dashboard.jsx / .css   # Post management table (auth required)
│   │   │   └── PostEditor.jsx / .css  # Full markdown editor (auth required)
│   │   ├── App.jsx              # Router + layout
│   │   ├── main.jsx             # React entry point
│   │   └── index.css            # Global CSS variables + base styles
│   ├── vite.config.js           # Vite config + /api proxy
│   └── package.json
│
├── start-backend.sh             # Shortcut: starts Django on :8000
├── start-frontend.sh            # Shortcut: starts Vite on :5173
└── DOCUMENTATION.md             # This file
```

---

## 4. Setup & Installation

### Prerequisites

- Python 3.10+
- Node.js 18+
- pip

### Backend setup

```bash
cd blog/backend

# Install Python dependencies
pip install django djangorestframework djangorestframework-simplejwt \
            django-cors-headers django-filter pillow pyyaml

# Run migrations
python manage.py migrate

# Create a superuser interactively
python manage.py createsuperuser

# Seed sample posts (optional; credentials must be supplied explicitly)
export BLOG_ADMIN_USERNAME=admin
export BLOG_ADMIN_PASSWORD='replace-with-a-strong-password'
export BLOG_ADMIN_EMAIL=admin@example.com
python seed_posts.py

# Start development server
python manage.py runserver
# → http://localhost:8000
```

### Frontend setup

```bash
cd blog/frontend

npm install
npm run dev
# → http://localhost:5173
```

### Shortcut scripts

```bash
# From the blog/ root directory:
./start-backend.sh    # Django on :8000
./start-frontend.sh   # Vite on :5173
```

The Vite dev server proxies all `/api/*` and `/media/*` requests to `http://localhost:8000`, so no CORS issues in development.

---

## 5. Backend Reference

### 5.1 Database Models

#### `Category`

| Field         | Type        | Notes                              |
|---------------|-------------|------------------------------------|
| `name`        | CharField   | Unique                             |
| `slug`        | SlugField   | Auto-generated from name           |
| `description` | TextField   | Optional                           |
| `color`       | CharField   | Hex color, default `#a855f7`       |
| `created_at`  | DateTime    | Auto                               |

#### `Tag`

| Field  | Type      | Notes                    |
|--------|-----------|--------------------------|
| `name` | CharField | Unique, stored lowercase |
| `slug` | SlugField | Auto-generated           |

#### `Post`

| Field          | Type          | Notes                                                   |
|----------------|---------------|---------------------------------------------------------|
| `id`           | UUIDField     | Primary key, auto-generated                             |
| `title`        | CharField     | Max 250 chars                                           |
| `slug`         | SlugField     | Auto from title, collision-safe (`title-1`, `title-2`)  |
| `author`       | FK → User     | `CASCADE` on delete                                     |
| `category`     | FK → Category | `SET_NULL` on delete                                    |
| `tags`         | M2M → Tag     | Optional                                                |
| `excerpt`      | TextField     | Max 500. Auto-filled from first 400 chars if left blank |
| `content`      | TextField     | Full Markdown                                           |
| `cover_image`  | ImageField    | Uploaded to `media/covers/`                             |
| `status`       | CharField     | `draft` or `published`                                  |
| `difficulty`   | CharField     | `beginner`, `intermediate`, `advanced`                  |
| `is_featured`  | BooleanField  | Shown in featured section on home page                  |
| `views`        | PositiveInt   | Incremented on each detail fetch                        |
| `read_time`    | SmallInt      | Minutes, set manually                                   |
| `published_at` | DateTime      | Set automatically on first publish                      |
| `created_at`   | DateTime      | Auto                                                    |
| `updated_at`   | DateTime      | Auto                                                    |

#### `Comment`

| Field          | Type      | Notes                                 |
|----------------|-----------|---------------------------------------|
| `post`         | FK → Post | `CASCADE`                             |
| `author_name`  | CharField |                                       |
| `author_email` | EmailField| Stored for moderation; never returned by the public API |
| `body`         | TextField |                                       |
| `is_approved`  | Boolean   | Only approved comments shown publicly |
| `created_at`   | DateTime  | Auto                                  |

Comments must be approved via Django Admin (`/admin/`) before they appear on the post.

#### `Newsletter`

| Field           | Type      | Notes           |
|-----------------|-----------|-----------------|
| `email`         | EmailField| Unique          |
| `subscribed_at` | DateTime  | Auto            |
| `is_active`     | Boolean   | Default `True`  |

#### `Profile` (accounts app)

One-to-one extension of Django's built-in `User`.

| Field     | Type       | Notes                   |
|-----------|------------|-------------------------|
| `user`    | OneToOne   | `CASCADE`               |
| `bio`     | TextField  | Shown on post detail     |
| `avatar`  | ImageField | Uploaded to `media/avatars/` |
| `github`  | URLField   |                         |
| `twitter` | URLField   |                         |
| `website` | URLField   |                         |

---

### 5.2 API Endpoints

All endpoints are prefixed with `/api/`.

#### Blog — public (no auth required)

| Method | Endpoint                            | Description                                             |
|--------|-------------------------------------|---------------------------------------------------------|
| GET    | `/blog/posts/`                      | Paginated list of published posts. Supports filters, search, ordering (see below) |
| GET    | `/blog/posts/featured/`             | Up to 6 featured published posts                        |
| GET    | `/blog/posts/<slug>/`               | Full post detail + approved comments. Increments `views` |
| POST   | `/blog/posts/<slug>/comments/`      | Submit a comment (pending approval)                     |
| GET    | `/blog/categories/`                 | All categories with post counts                         |
| GET    | `/blog/categories/<slug>/`          | Single category detail                                  |
| GET    | `/blog/tags/`                       | All tags                                                |
| GET    | `/blog/search/?q=<query>`           | Full-text search across title, excerpt, content, tags   |
| GET    | `/blog/stats/`                      | `{ total_posts, total_categories, total_tags, total_views }` |
| POST   | `/blog/newsletter/`                 | Subscribe email `{ "email": "..." }`                    |

##### Post list filters

Append as query parameters to `GET /blog/posts/`:

| Parameter          | Example                          | Description              |
|--------------------|----------------------------------|--------------------------|
| `category__slug`   | `?category__slug=ctf-writeups`   | Filter by category       |
| `tags__slug`       | `?tags__slug=python`             | Filter by tag            |
| `difficulty`       | `?difficulty=advanced`           | Filter by difficulty     |
| `is_featured`      | `?is_featured=true`              | Featured posts only      |
| `search`           | `?search=sql+injection`          | Full-text search         |
| `ordering`         | `?ordering=-views`               | Sort field (prefix `-` for desc) |
| `page`             | `?page=2`                        | Pagination (12 per page) |
| `page_size`        | `?page_size=50`                  | Page size override (maximum 100) |

Valid `ordering` values: `published_at`, `views`, `created_at`, `read_time`.

#### Blog — authenticated (JWT Bearer required)

| Method | Endpoint                    | Description                               |
|--------|-----------------------------|-------------------------------------------|
| GET    | `/blog/posts/mine/`         | All posts by the current user (incl. drafts) |
| POST   | `/blog/posts/create/`       | Create a new post                         |
| GET    | `/blog/posts/<slug>/edit/`  | Get post for editing (author only)        |
| PATCH  | `/blog/posts/<slug>/edit/`  | Partially update a post (author only)     |
| PUT    | `/blog/posts/<slug>/edit/`  | Full update a post (author only)          |
| DELETE | `/blog/posts/<slug>/edit/`  | Delete a post (author only)               |

##### Post create / update payload

```json
{
  "title": "My Post Title",
  "category": 3,
  "tags_by_name": ["python", "web", "ctf"],
  "excerpt": "Short summary shown in cards.",
  "content": "## Markdown content here...",
  "status": "draft",
  "difficulty": "intermediate",
  "is_featured": false,
  "read_time": 10,
  "published_at": null
}
```

- `tags_by_name` accepts tag name strings — the API creates any missing tags automatically.
- `category` accepts a category integer ID (from `GET /api/blog/categories/`).
- Setting `status` to `published` automatically sets `published_at` to now if not already set.

#### Auth endpoints

| Method | Endpoint                  | Description                                          |
|--------|---------------------------|------------------------------------------------------|
| POST   | `/auth/login/`            | `{ username, password }` → `{ access, refresh, user }` |
| POST   | `/auth/token/refresh/`    | `{ refresh }` → `{ access }`                        |
| GET    | `/auth/me/`               | Current user info (requires auth)                    |
| GET    | `/auth/profile/`          | Current user's profile (requires auth)               |
| PATCH  | `/auth/profile/`          | Update bio, avatar, github, twitter, website         |

---

### 5.3 Authentication

The API uses **JWT Bearer tokens**.

- **Access token** — valid for 1 hour. Sent in `Authorization: Bearer <token>` header.
- **Refresh token** — valid for 7 days. Used to get a new access token via `/auth/token/refresh/`.
- `ROTATE_REFRESH_TOKENS = True` — a new refresh token is issued each time you refresh.
- The frontend stores the replacement refresh token whenever rotation occurs.

The Axios client in `frontend/src/api/client.js` handles token injection and automatic silent refresh. If a request gets a `401`, it automatically calls the refresh endpoint and retries the original request once.

---

### 5.4 Configuration

Key environment-driven settings in `backend/config/settings.py`:

```python
DEBUG = env_bool('DJANGO_DEBUG', True)
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1')

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
}

CORS_ALLOWED_ORIGINS = os.environ.get(
    'DJANGO_CORS_ALLOWED_ORIGINS',
    'http://localhost:5173',
)

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'   # Uploaded files stored here
```

For production, set:
- `DJANGO_DEBUG=false`
- `DJANGO_SECRET_KEY` to a long random value (startup fails without it when debug is disabled)
- `DJANGO_ALLOWED_HOSTS` to a comma-separated host list
- `DJANGO_CORS_ALLOWED_ORIGINS` to comma-separated frontend origins
- HTTPS redirect, secure cookies, and one-year HSTS are enabled automatically when debug is disabled
- Set `DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS=true` and `DJANGO_SECURE_HSTS_PRELOAD=true` only when every subdomain is permanently HTTPS-ready
- `DATABASES` to PostgreSQL

Copy `.env.example` as a reference. Django and Vite read process environment
variables; export them in your shell or configure them in your process manager.

---

## 6. Frontend Reference

### 6.1 Pages & Routes

| Route                   | Component         | Auth | Description                                   |
|-------------------------|-------------------|------|-----------------------------------------------|
| `/`                     | `Home`            | No   | Hero, stats, featured posts, categories, newsletter |
| `/posts`                | `PostList`        | No   | Filterable, searchable post grid with sidebar  |
| `/posts/:slug`          | `PostDetail`      | No   | Full post view with markdown, comments form    |
| `/categories`           | `Categories`      | No   | All categories as cards                        |
| `/categories/:slug`     | `CategoryDetail`  | No   | All posts in a category                        |
| `/about`                | `About`           | No   | Bio, skills table, fun facts, terminal widget  |
| `/contact`              | `Contact`         | No   | Contact info + message form                    |
| `/login`                | `Login`           | No   | JWT login form                                 |
| `/dashboard`            | `Dashboard`       | Yes  | Post management table (edit, delete, new)      |
| `/editor/new`           | `PostEditor`      | Yes  | Full-screen markdown editor — create new post  |
| `/editor/:slug`         | `PostEditor`      | Yes  | Full-screen markdown editor — edit existing    |

The editor routes render without Navbar/Footer (full-screen layout). All other routes share the shell layout.

### 6.2 Components

#### `Navbar`
Sticky, blurs on scroll. Shows public nav links (`#home`, `#posts`, `#categories`, `#about`, `#contact`). When authenticated, replaces the login button with the username (links to `/dashboard`), a **+ write** button, and a logout button. Collapses to a hamburger menu on mobile.

#### `Footer`
Rendered below all pages (except the editor). Shows logo, tagline, nav links grouped into two columns, copyright.

#### `PostCard`
Used in all post grids. Displays cover image (if any), category with its color, difficulty badge, title, excerpt (3-line clamp), tag pills, date, read time, and a "Read →" link.

#### `ProtectedRoute`
Wraps any route that requires login. Shows `Spinner` while auth state loads, redirects to `/login` if no user.

#### `Spinner`
Centered animated ring, used during data fetching.

### 6.3 API Client

`frontend/src/api/client.js` exports two objects:

```js
blogApi.getPosts(params)          // GET /blog/posts/ with query params
blogApi.getPost(slug)             // GET /blog/posts/:slug/
blogApi.getFeatured()             // GET /blog/posts/featured/
blogApi.getCategories()           // GET /blog/categories/
blogApi.getCategory(slug)         // GET /blog/categories/:slug/
blogApi.getTags()                 // GET /blog/tags/
blogApi.search(q)                 // GET /blog/search/?q=
blogApi.getStats()                // GET /blog/stats/
blogApi.addComment(slug, data)    // POST /blog/posts/:slug/comments/
blogApi.subscribe(email)          // POST /blog/newsletter/
blogApi.myPosts()                 // GET /blog/posts/mine/    (auth)
blogApi.createPost(data)          // POST /blog/posts/create/ (auth)
blogApi.getPostForEdit(slug)      // GET /blog/posts/:slug/edit/  (auth)
blogApi.updatePost(slug, data)    // PATCH /blog/posts/:slug/edit/ (auth)
blogApi.deletePost(slug)          // DELETE /blog/posts/:slug/edit/ (auth)

authApi.login(data)               // POST /auth/login/
authApi.me()                      // GET /auth/me/
```

The Axios instance automatically attaches the `Authorization: Bearer <token>` header to every request and silently refreshes the access token on `401` responses. Its base URL comes from `VITE_API_BASE_URL`, defaulting to the same-origin `/api`.

### 6.4 Auth Context

`AuthContext` wraps the entire app and provides:

```js
const { user, loading, login, logout } = useAuth()
```

| Value     | Type       | Description                                        |
|-----------|------------|----------------------------------------------------|
| `user`    | Object/null| The logged-in user, or `null`                      |
| `loading` | Boolean    | True while verifying token on page load             |
| `login`   | Function   | Takes `{ username, password }`, stores tokens, sets user |
| `logout`  | Function   | Clears tokens from localStorage, sets user to null |

On page load, if a token exists in `localStorage`, the context calls `GET /auth/me/` to verify it and hydrate the user state.

### 6.5 Theme & Styling

All theme tokens are CSS custom properties defined in `frontend/src/index.css`:

```css
--bg-primary:    #2d2d3b   /* main background */
--bg-secondary:  #252534   /* navbar, footer, editor sidebar */
--bg-card:       #333344   /* post cards, info boxes */
--bg-hover:      #3d3d50   /* hover state */

--text-primary:  #ffffff
--text-secondary:#94a3b8
--text-muted:    #64748b

--accent:        #a855f7   /* purple — links, highlights, borders */
--accent-dim:    rgba(168, 85, 247, 0.15)
--accent-border: rgba(168, 85, 247, 0.5)

--danger:        #ef4444
--success:       #22c55e
--warning:       #f97316
--info:          #3b82f6

--mono: 'JetBrains Mono', 'Fira Code', ui-monospace, monospace
--radius: 8px
--radius-sm: 4px
--transition: 0.2s ease
```

Each page and component has its own scoped `.css` file. Shared utility classes (`container`, `btn`, `input`, `tag`, `accent`, `text-muted`) live in `index.css`.

---

## 7. Writing Posts

### 7.1 In-browser Editor

The fastest way to write and publish without leaving the browser.

1. Log in at `/login`
2. Click **+ write** in the navbar, or go to `/editor/new`
3. Type your title in the top bar input
4. Write markdown in the main editor pane
5. Fill in the right sidebar:
   - **Category** — dropdown of existing categories
   - **Tags** — comma-separated names (new tags are created automatically)
   - **Difficulty** — beginner / intermediate / advanced
   - **Read time** — estimated minutes
   - **Excerpt** — 1–2 sentence summary shown in post cards
   - **Featured** — tick to show in the featured section on the homepage
   - **Status** — draft / published
6. **Save draft** — saves without publishing, you can return later
7. **Publish →** — saves with `status=published` and redirects to the live post

Toggle the editor view with the **edit / live / preview** buttons at the bottom right:
- `edit` — editor only
- `live` — side-by-side editor + rendered preview
- `preview` — rendered preview only

### 7.2 Dashboard

`/dashboard` — only accessible when logged in.

Shows a table of all your posts (including drafts) with:

| Column     | Description                                  |
|------------|----------------------------------------------|
| Title      | Clickable link to the live post (new tab)    |
| Category   |                                              |
| Status     | `published` (green) or `draft` (orange)      |
| Difficulty |                                              |
| Views      | Total view count                             |
| Date       | Published date, or created date for drafts   |
| Actions    | **edit** → opens editor · **delete** → confirms then removes |

### 7.3 Obsidian / Markdown Import

For writeups prepared offline in Obsidian or any markdown editor, use the management command:

```bash
cd blog/backend
python manage.py import_post path/to/your-note.md [options]
```

| Option     | Description                                            |
|------------|--------------------------------------------------------|
| `--publish`| Immediately set status to `published`                  |
| `--update` | If a post with the same title exists, update it instead of erroring |
| `--author` | Username to assign as author (default: `admin`)        |

#### YAML frontmatter (optional)

Place this at the very top of your `.md` file. All fields are optional — the command falls back to sensible defaults if they are missing.

```yaml
---
title: "HTB: Forest — Kerberoasting Walkthrough"
category: CTF Writeups
tags: [ctf, active-directory, windows, kerberos]
difficulty: advanced
status: published
read_time: 20
excerpt: "Full walkthrough of the Forest HackTheBox machine."
featured: true
---

## Content starts here
```

| Frontmatter key | Default if omitted              |
|-----------------|---------------------------------|
| `title`         | Filename (dashes/underscores → spaces, title-cased) |
| `category`      | None (created automatically if new) |
| `tags`          | Empty list                      |
| `difficulty`    | `beginner`                      |
| `status`        | `draft` (or `published` if `--publish` flag is used) |
| `read_time`     | Estimated from word count (words ÷ 200) |
| `excerpt`       | Empty (auto-filled from first 400 chars by the model) |
| `featured`      | `false`                         |

#### Examples

```bash
# Import as draft, review before publishing
python manage.py import_post ~/notes/my-writeup.md

# Import and publish immediately
python manage.py import_post ~/notes/my-writeup.md --publish

# Re-import after editing the file
python manage.py import_post ~/notes/my-writeup.md --update --publish

# Assign to a specific author
python manage.py import_post ~/notes/my-writeup.md --author wh1t3r4v3n --publish
```

#### What markdown renders correctly

The frontend uses `react-markdown` with `remark-gfm` and `rehype-highlight`. These render correctly:

- All standard CommonMark (headers, bold, italic, lists, blockquotes, links, images)
- **GFM extensions**: tables, strikethrough, task lists (`- [ ]`), autolinks
- **Code blocks** with syntax highlighting (specify language after the triple backtick)
- Horizontal rules, inline code

The only Obsidian-specific syntax that **will not render** is `[[wikilinks]]` and `![[embeds]]`. Use standard markdown links `[text](url)` and images `![alt](url)` instead.

---

## 8. Deployment

Production deployment follows **Server Directory Structure Amendment v1.0**:

- Release source: `/var/www/apps/whiteraven-blog/releases/<timestamp>/`
- Active release: `/var/www/apps/whiteraven-blog/current`
- Logs: `/var/www/logs/whiteraven-blog/`
- Backups: `/var/www/backups/{db,releases}/whiteraven-blog/`
- Temporary files: `/var/www/tmp/whiteraven-blog/`
- Operational scripts: `/var/www/scripts/whiteraven-blog/`
- Persistent media/static/config: `/var/www/shared/whiteraven-blog/`

The repository includes production systemd, Nginx, logrotate, deployment,
backup, and rollback assets under `deploy/`. Follow `DEPLOYMENT.md` for the
complete first-deploy and routine operations runbook.

---

## 9. Environment & Seed Credentials

The repository contains no default password. `seed_posts.py` requires credentials
through environment variables:

```bash
export BLOG_ADMIN_USERNAME=admin
export BLOG_ADMIN_PASSWORD='replace-with-a-strong-password'
export BLOG_ADMIN_EMAIL=admin@example.com
python backend/seed_posts.py
```

Django admin panel: `http://localhost:8000/admin/`

Change the password:
```bash
cd backend
python manage.py changepassword admin
```
