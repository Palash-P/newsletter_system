# 📰 Newsletter System

A complete newsletter/email campaign system built with Django, Celery, Redis, and PostgreSQL. Similar to Mailchimp Lite — supports subscriber management, email campaigns, open/click tracking, and analytics.

**Live Demo:** https://web-production-32fe7.up.railway.app

---

## 🚀 Features

- **Subscriber Management** — Subscribe, double opt-in email verification, unsubscribe via token
- **Newsletter Creation** — Create HTML newsletters via REST API
- **Async Email Sending** — Celery sends emails in batches of 100 in the background
- **Open Tracking** — Invisible 1x1 tracking pixel records when emails are opened
- **Click Tracking** — Link wrapping records clicks and redirects to original URL
- **Analytics** — Open rates, click rates, delivery stats cached in Redis

---

## 🛠️ Tech Stack

| Technology | Purpose |
|------------|---------|
| Django + DRF | API framework |
| PostgreSQL | Data storage |
| Redis | Caching + Celery broker |
| Celery | Async email sending |
| Gunicorn | Production WSGI server |
| Railway | Deployment |

---

## 📡 API Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/subscribe/` | Subscribe to newsletter | Public |
| GET | `/api/verify/<token>/` | Verify email (double opt-in) | Public |
| GET | `/api/unsubscribe/<token>/` | Unsubscribe | Public |
| GET | `/api/newsletters/` | List newsletters | Admin |
| POST | `/api/newsletters/` | Create newsletter | Admin |
| POST | `/api/newsletters/<id>/send/` | Send newsletter | Admin |
| GET | `/api/analytics/` | Get stats (cached) | Admin |
| GET | `/api/track/open/<id>/` | Track email open | Public |
| GET | `/api/track/click/<id>/` | Track link click | Public |

---

## ⚙️ Local Setup

### Prerequisites
- Python 3.10+
- Docker Desktop (for Redis)

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/newsletter-system.git
cd newsletter-system
```

### 2. Create virtual environment
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure environment variables
```bash
cp .env.example .env
# Edit .env with your values
```

### 4. Start Redis
```bash
docker run -d -p 6379:6379 --name redis redis:7
```

### 5. Run migrations
```bash
python manage.py migrate
python manage.py createsuperuser
```

### 6. Start all services (3 terminals)

**Terminal 1 — Django:**
```bash
python manage.py runserver
```

**Terminal 2 — Celery Worker:**
```bash
celery -A config worker --loglevel=info --pool=solo
```

**Terminal 3 — Test requests**

---

## 🧪 Testing the API

### Subscribe
```bash
curl -X POST http://127.0.0.1:8000/api/subscribe/ \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "name": "Test User"}'
```

### Create Newsletter (admin)
```bash
curl -X POST http://127.0.0.1:8000/api/newsletters/ \
  -u admin:password \
  -H "Content-Type: application/json" \
  -d '{"title": "Issue #1", "content": "<h1>Hello!</h1><p>Welcome.</p>"}'
```

### Send Newsletter (admin)
```bash
curl -X POST http://127.0.0.1:8000/api/newsletters/1/send/ \
  -u admin:password
```

### Get Analytics (admin)
```bash
curl http://127.0.0.1:8000/api/analytics/ -u admin:password
```

---

## 🏗️ Project Structure

```
newsletter_system/
├── config/
│   ├── settings.py     ← All Django settings
│   ├── urls.py         ← URL routing
│   └── celery.py       ← Celery configuration
├── newsletters/
│   ├── models.py       ← Subscriber, Newsletter, Campaign
│   ├── views.py        ← API endpoints
│   ├── serializers.py  ← Input validation + JSON shaping
│   ├── tasks.py        ← Celery async tasks
│   └── admin.py        ← Django admin configuration
├── Procfile            ← Railway deployment commands
├── requirements.txt
└── .env.example
```

---

## 🗄️ Data Models

```
Subscriber          Newsletter
    │                   │
    └──── Campaign ──────┘
              │
         opened? clicked?
         sent_at? failed?
```

**Subscriber** — email, name, active status, verification/unsubscribe tokens

**Newsletter** — title, HTML content, status (draft → sending → sent)

**Campaign** — one record per subscriber per newsletter, tracks delivery + engagement

---

## 🚀 Deployment (Railway)

1. Push to GitHub
2. Create new project on [railway.app](https://railway.app) → Deploy from GitHub
3. Add PostgreSQL and Redis services
4. Set environment variables:
```
SECRET_KEY=your-secret-key
DEBUG=False
DATABASE_URL=<from Railway PostgreSQL>
REDIS_URL=<from Railway Redis>
```
5. Add pre-deploy command: `python manage.py migrate`
6. Deploy!

---

## 📊 How Tracking Works

**Open Tracking:**
Every email contains an invisible 1x1 GIF image. When the email client loads it, our server records the open.

**Click Tracking:**
All links are wrapped with a redirect URL. When clicked, our server records it then redirects to the original URL.

**Analytics Caching:**
Analytics results are cached in Redis for 5 minutes to avoid hammering the database on every request.

---

## 🔑 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `SECRET_KEY` | Django secret key | Yes |
| `DEBUG` | Debug mode (False in production) | Yes |
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `REDIS_URL` | Redis connection string | Yes |
| `EMAIL_BACKEND` | Email backend class | No |
| `SENDGRID_API_KEY` | SendGrid API key for real emails | No |

---

## 📝 License

MIT
