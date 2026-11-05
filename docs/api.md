# AFEWS REST API (for the resident mobile app)

Base URL while developing: `http://<laptop-address>:8000/api/`

All bodies and responses are JSON. After signing in, send the token on every
request in a header: `Authorization: Token <token>`.

| Method | Path | Needs token | What it does |
|---|---|---|---|
| GET | `/zones/` | No | List zones (`id`, `zone_name`, `ward`) for the sign-up screen |
| POST | `/auth/register/` | No | Create a resident account. Returns `token` and `user` |
| POST | `/auth/login/` | No | Sign in. Returns `token` and `user` |
| POST | `/auth/logout/` | Yes | Invalidate the token |
| GET | `/me/` | Yes | The signed-in user and their zone |
| GET | `/my-zone/` | Resident | Zone, current risk (with advice) and the 5 latest alerts |
| GET | `/alerts/` | Resident | All alerts for the resident's zone, 20 per page (`?page=2`) |
| POST | `/alerts/<id>/feedback/` | Resident | Rate an alert 1 to 5, optional `comment` |

## Register

```json
POST /api/auth/register/
{ "full_name": "Grace Achieng", "phone_number": "0712345678",
  "zone": 1, "username": "grace", "password": "a-strong-password" }
```

`201` returns `{ "token": "...", "user": { ... } }`.
`400` returns `{ "errors": { "phone_number": ["..."], ... } }`.
Phone numbers are stored as `+2547...`. The role is always `RESIDENT`.

## Sign in

```json
POST /api/auth/login/
{ "username": "grace", "password": "a-strong-password" }
```

`200` returns `{ "token": "...", "user": { ... } }`. `400` means wrong username or password.
Sign-in and sign-up are limited to 30 requests a minute (`429` after that).

## My zone

```json
GET /api/my-zone/
{
  "zone": { "id": 1, "zone_name": "Kibera - Gatwekera", "ward": "Kibera" },
  "risk": { "level": "HIGH", "label": "High", "confidence": 0.75,
            "advice": "Move valuables ...", "predicted_at": "2026-11-03T16:49:01Z" },
  "alerts": [ { "id": 1, "message": "...", "risk_level": "HIGH",
                "risk_label": "High", "sent_at": "...", "feedback_rating": null } ]
}
```

`risk` is `null` until officers run the first prediction. Times are UTC.

## Status codes

`401` no or invalid token. `403` signed in but not a resident. `404` alert not in your zone. `429` too many attempts.
