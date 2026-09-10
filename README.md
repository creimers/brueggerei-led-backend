# 🌊 Brüggerei LED Backend

Django app that manages the content of the LED matrix. The admin edits the
content, the hardware polls `/api/content.txt`.

## Development

Everything runs inside Docker Compose (`docker-compose.yml`):

```sh
make build        # build the image (again after uv.lock changes)
make runserver    # migrate, then runserver on http://localhost:8000
make superuser    # admin login
make test
```

Running natively works too (`uv sync`, `python manage.py runserver`); no
`.env` is needed in development.

## Production (VM)

`production.yml` follows the pattern of the other sites on the VM: the app
container sits behind the shared Traefik (external `web` network,
`letsencrypt` resolver, `websecure` entrypoint), an `nginx:alpine` sidecar
serves `/static/` from the bind-mounted `staticfiles/` directory, and the
SQLite database lives in the bind-mounted `data/` directory. Traefik routes
`genossenschaftsmatrix.superservice-international.com` to the app.

`.env` on the VM needs (see `.env.example`):

| Variable | Meaning |
|----------|---------|
| `DJANGO_SECRET_KEY` | Generate with `python -c "from django.core.management.utils import get_random_secret_key as k; print(k())"` |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated hostnames, e.g. `genossenschaftsmatrix.superservice-international.com`. Also used for `CSRF_TRUSTED_ORIGINS` and the healthcheck. |
| `SITE_HOST` | Optional. Hostname in the Traefik labels, defaults to `genossenschaftsmatrix.superservice-international.com`. |

Production assumes a TLS-terminating reverse proxy that sets
`X-Forwarded-Proto` (Traefik does); without that header the HTTPS redirect
would loop.

### First deploy / migration from the old VM

1. Clone the repo on the VM, create `.env`.
2. Copy the database from the old VM into `data/`:
   `scp old-vm:/path/to/webapp/db.sqlite3 data/db.sqlite3`
3. `docker compose -f production.yml up -d --build`

To try the stack before the DNS switchover, point a temporary hostname at
the VM and set

```sh
SITE_HOST=next.genossenschaftsmatrix.superservice-international.com
DJANGO_ALLOWED_HOSTS=next.genossenschaftsmatrix.superservice-international.com
```

For the switchover, remove `SITE_HOST` again, set `DJANGO_ALLOWED_HOSTS`
to the real hostname, then `make rollout` and
`docker compose -f production.yml up -d nginx` (the sidecar carries the
static router labels, and `make rollout` only recreates `django`). Traefik
picks up the new labels and requests the certificate.

### Deploying

```sh
make rollout      # build the image, then `docker rollout` the django service
```

`start.sh` runs migrations and `collectstatic` before starting gunicorn.
The container only reports healthy once `GET /-/health/` answers, so
`docker rollout` starts the new container next to the old one, waits for
the healthcheck, and stops the old one after a drain period.

### Backups

The whole state is `data/db.sqlite3`; include it in the VM backup routine.
