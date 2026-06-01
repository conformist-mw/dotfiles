# Auth migration + role split — plan

Замена oauth2-proxy на **tinyauth + CrowdSec** (всё своё, без Cloudflare, без SMTP) и распил
перегруженной роли `segments`. Все изменения — на **hetzner**; bee трогаем только чисткой архива.

Контекст и обоснование выбора — в worksheet (`cf-migration-worksheet.md`) и в памяти.

---

## 1. Распил роли `segments`

Сейчас `roles/segments` делает сразу: Traefik (ingress), oauth2-proxy (auth), whoami (тест),
segments-go (сам сервис), pihole (DNS). Разносим по ответственности:

| Новая роль | Что переезжает из segments | Назначение |
|---|---|---|
| **`traefik-vps`** (new) | `files/traefik.yml`, `templates/dynamic.yml`, контейнер Traefik, `HETZNER_API_TOKEN`, letsencrypt + logs volumes | публичный ingress (80+443, TLS, middlewares) |
| **`tinyauth`** (new) | — (заменяет oauth2-proxy) | auth-гейт: локальные ты+жена, per-app ACL |
| **`crowdsec`** (new) | — (новое) | защита от перебора/сканов + community blocklist |
| **`pihole`** (new) | `files/pihole-dnsmask.conf`, контейнер pihole | DNS + split-DNS `*.bee.home` для WG |
| **`segments`** (slim) | контейнер segments-go | только сам сервис |
| ~~oauth2-proxy~~ | удаляется | → tinyauth |
| ~~whoami~~ | удаляется | тестовый, не нужен |

**Чистка по ходу:** `roles/segments/vars/main.yml` содержит `django_vars` и `network: traefik_net` —
это похоже на остатки (segments-go их не использует, контейнер ходит в `{{ docker_network }}`).
Проверить и выпилить при слиме.

### Именование Traefik-роли — нужно твоё решение

Сейчас уже есть роль `traefik` (для bee, plain http :80). Варианты, чтобы «без непоняток»:

- **(A, рекомендую)** оставить `traefik` за bee, новую назвать `traefik-vps`. Минимум правок.
- **(B, симметрично)** переименовать bee-роль в `traefik-home` + новая `traefik-vps`. Чище семантически, но трогает `beelink.yml`.

> Выбрать A или B → от этого зависят имена в плейбуках ниже (пишу как A).

### Извлечение pihole — подтверди

Ты просил вынести только Traefik, но pihole в `segments` — такой же чужеродный жилец.
Рекомендую вынести в роль `pihole` заодно (он — backbone split-DNS для VPN-доступа к immich и пр.).
Если не хочешь сейчас — оставим в segments, но это против «без непоняток».

---

## 2. Целевая схема auth/защиты на hetzner

```
                   ┌─ entryPoint websecure: middleware crowdsec@... (ВСЁ проходит через CrowdSec)
internet → Traefik ┤
                   ├─ auth-chain   = [tinyauth@docker, security-headers, rate-limit, compression]   ← бесправные
                   └─ no-auth-chain = [rate-limit, compression]                                       ← со своей auth / публичные
```

- **CrowdSec** вешаем на **entryPoint** `websecure` (Traefik static config) — тогда он покрывает
  все публичные маршруты независимо от роутера (включая HA/navidrome, проксируемые из дома).
- **tinyauth** заменяет `oauth2-proxy@docker` внутри `auth-chain`. Имя цепочки `auth-chain`
  **сохраняем** → app-роли и дефолтный лейбл в `inventory.yml` не меняются.
- **Per-app ACL** (tinyauth): добавляем шаблонный лейбл на app-роли, значение из
  `app_allow_users | default('oleg')`. lessons/home-meters → `"oleg,wife"`, остальные → `oleg`.
  > Точный формат лейбла tinyauth (`tinyauth.apps.<app>.users.allow`) и как tinyauth матчит «app»
  > — сверить с доками на Фазе 2 на одном сервисе.

### Раскладка по сервисам (hetzner)

| Сервис | Цепочка | allow |
|---|---|---|
| lessons | auth-chain + bypass-роутер для `/tgwebhook` (без auth) | oleg, wife |
| home-meters | auth-chain | oleg, wife |
| rsstt | auth-chain | oleg |
| homepage (vps) | auth-chain | oleg |
| dozzle (vps) | auth-chain | oleg |
| segments | no-auth-chain | — |
| commeilfaut | no-auth-chain (+ tg-хуки открыты) | — |
| HA (проксируется из дома) | no-auth-chain (своя 2FA) | — |
| navidrome (если выставляем) | no-auth-chain (своя auth) | — |

> bee — публично НЕ светит, его homepage/dozzle остаются LAN/VPN (через WG). Если захочешь
> bee-dozzle удалённо без VPN — добавим отдельный published-роут через hetzner под auth-chain (опц.).

---

## 3. Фазы (де-рискованно: рефактор отдельно от смены auth)

### Фаза 0 — Чистка архива (низкий риск, независимо)
- Архив-каталог уже есть: `roles/outdated/` (там лежат uptime-kuma, ipython, homer, paperless, hackmd, lidarr).
- Переместить туда роли: `gitea`, `pgadmin`, `portainer`, `weblist`, `redis` (bee) +
  `memos`, `flatnotes` (hetzner). `git mv roles/<name> roles/outdated/<name>`.
- Убрать из `hetzner.yml`: строки `memos`, `flatnotes`. Из `beelink.yml`: `gitea`, `pgadmin`,
  `portainer`, `weblist`, `redis`. **В плейбуках не должно остаться никаких следов архивных ролей.**
- `whoami` — не роль, а inline-таска в `segments/tasks/main.yml` → просто удалить таску.
- Убрать `router`-маршрут из dynamic.yml (не используется).
- Снести контейнеры с хостов: `memos`, `notes`, `whoami`, `gitea`, `pgadmin`, `portainer`,
  `weblist`, `redis`.
- (Вне скоупа, на заметку) в `roles/` валяются нигде не используемые роли: `actual`,
  `filebrowser`, `filestash`, `jellyseerr`, `minidlna`, `monitoring`, `nextcloud`,
  `photoprism`, `syncthing` — при желании туда же, в `roles/outdated/`.

### Фаза 1 — Рефактор без смены поведения
- Создать `traefik-vps`, `pihole`, слим-`segments`, временную `oauth2-proxy` (вынести oauth2-бит
  из segments в отдельную роль как есть — чтобы auth продолжал работать).
- Обновить `hetzner.yml`: `traefik-vps` → в Infrastructure; `oauth2-proxy`, `pihole` рядом;
  `segments` остаётся в Applications (только сервис).
- **Деплой, проверка: всё работает ровно как раньше** (oauth2 ещё на месте). Это контрольная точка.

### Фаза 2 — tinyauth + CrowdSec рядом, валидация на одном сервисе
- Роль `tinyauth`: контейнер + юзеры (ты+жена, bcrypt-хеши; TOTP опц. через QR). **Почта не нужна.**
- Роль `crowdsec`: агент (читает `/var/log/traefik/access.log`), коллекции
  `crowdsecurity/traefik`, `crowdsecurity/base-http-scenarios`, `crowdsecurity/http-cve`,
  community blocklist; bouncer-API-key. Плагин-bouncer в static config `traefik-vps`.
- Завести middleware `tinyauth@docker` и временную цепочку `tinyauth-chain`.
- Перевести **один** сервис (напр. `rsstt`) на `tinyauth-chain`, проверить: логин, ACL, TOTP, бан CrowdSec.

### Фаза 3 — Cut over auth
- Переопределить содержимое `auth-chain`: `oauth2-proxy@docker` → `tinyauth@docker`.
- Проставить per-app `app_allow_users` (lessons/home-meters = `oleg,wife`, прочие = `oleg`).
- Сохранить bypass-роутер `/tgwebhook` для lessons (без auth, секрет в пути).
- Проверить каждый защищённый сервис + жена логинится в lessons/home-meters и НЕ видит остальное.

### Фаза 4 — Декомиссия oauth2-proxy
- Удалить роль `oauth2-proxy`, `authenticated-emails.txt`, cookie-secret из Bitwarden-lookup.
- Убрать контейнер oauth2-proxy с хоста.

### Фаза 5 — Хардненинг и хвосты
- Убрать `watchtower` (оба хоста), **запиннить версии образов** вместо `:latest`
  (особенно публичные); авто-апдейт позже через Renovate при переезде на k3s.
- `postgres` на bee: прибить байндинг к `127.0.0.1`/docker-сети (сейчас `0.0.0.0:5432`).
- (Опц.) CrowdSec AppSec-компонент (WAF-правила) на entryPoint, если захочется глубже.
- pihole: при желании ужать до минимального dnsmasq/CoreDNS только под split-DNS
  (DNS-функцию не убивать, пока не заменим — от неё зависит VPN-доступ к `*.bee.home`).

---

## 4. Что НЕ трогаем
- WireGuard (hetzner↔дом) — остаётся как личный VPN во всю LAN.
- pihole split-DNS `*.bee.home` — backbone VPN-доступа (immich = `photos.bee.home`).
- bee целиком (кроме чистки архива) — он LAN-only, публично не светит.
- DNS-записи домена — остаются на текущем DNS, A на IP hetzner. Cloudflare не вводим.

---

## Решения (зафиксировано)
1. Имя Traefik-роли: **A** — `traefik` (bee) + `traefik-vps` (hetzner).
2. Pihole извлекаем в свою роль `pihole` — да.
3. Архив: `git mv` в существующий `roles/outdated/`. В плейбуках — **ноль следов** архивных ролей.
   В будущем `roles/outdated/` просто снесём.
