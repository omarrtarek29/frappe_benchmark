# Redis on a Separate Server

Move Frappe's Redis (cache, background jobs, real-time updates) off the app server onto its own machine.

---

## Your servers (example IPs)


| Server   | IP               | What runs there           |
| -------- | ---------------- | ------------------------- |
| App      | `95.xxx.xxx.222` | Frappe, Gunicorn, workers |
| Redis    | `95.xxx.xxx.223` | Redis only                |
| Database | `95.xxx.xxx.224` | MariaDB (see other guide) |


Frappe needs **3 Redis ports** on the Redis server:


| Port  | Used for                      |
| ----- | ----------------------------- |
| 11000 | Cache                         |
| 11001 | Background job queue          |
| 11002 | Socket.IO (live desk updates) |


---

## Do I need a separate Redis server?

**Yes, if you see:**

- Background jobs stuck in **Queued** for a long time
- Server runs out of **RAM** (OOM kills, heavy swap)
- Site slows down when many users are online
- You want more web workers but the same box is already full

**No, if:**

- Jobs finish quickly
- RAM usage is stable
- One server handles your traffic fine

There is no magic row count. Split when the **server is struggling**, not because the database is big.

---

## Why bother?

1. **More RAM for the app** — Redis memory does not fight with Frappe and MariaDB
2. **Faster web requests** — CPU on the app box is for HTTP, not Redis
3. **Safer** — a Redis spike is less likely to crash the whole site

---

## Step 1 — Set up the Redis server (`95.xxx.xxx.223`)

### Install Redis

```bash
sudo apt update
sudo apt install redis-server -y
```

### Open 3 ports (one config file per port, or your own setup)

Each instance needs:

```ini
bind 0.0.0.0
protected-mode no
maxmemory 3500mb
maxmemory-policy allkeys-lru
port 11000   # use 11001 and 11002 for the other two
```

### Allow only the app server (firewall)

```bash
sudo ufw allow ssh
sudo ufw allow from 95.xxx.xxx.222 to any port 11000 proto tcp
sudo ufw allow from 95.xxx.xxx.222 to any port 11001 proto tcp
sudo ufw allow from 95.xxx.xxx.222 to any port 11002 proto tcp
sudo ufw enable
```

Also add the same rules in your **cloud firewall** (security group).  
Never open ports 11000–11002 to the whole internet.

### Check Redis is listening

```bash
sudo ss -tpln | grep redis
```

You should see 11000, 11001, and 11002.

---

## Step 2 — Point Frappe at Redis (`95.xxx.xxx.222`)

Edit `sites/common_site_config.json`:

```json
{
  "redis_cache": "redis://95.xxx.xxx.223:11000",
  "redis_queue": "redis://95.xxx.xxx.223:11001",
  "redis_socketio": "redis://95.xxx.xxx.223:11002",
  "use_redis_auth": false
}
```

Restart:

```bash
cd ~/frappe-bench
bench clear-cache
bench restart
```

### Check it works

```bash
ss -tpon | grep 95.xxx.xxx.223
```

You should see **ESTAB** connections on all three ports.

### Background jobs still queued?

Redis is only half the story. You also need **worker processes** on the app server:

```bash
sudo supervisorctl status | grep worker
```

If many jobs stay queued, increase `numprocs` for the **long worker** in `config/supervisor.conf`, then restart supervisor.

---

## Common problems


| Problem             | Fix                                                             |
| ------------------- | --------------------------------------------------------------- |
| Jobs stay Queued    | Check firewall, `redis_queue` URL, and that workers are running |
| Connection refused  | Redis not running or wrong port — check on Redis server         |
| Desk feels slow     | Check `redis_cache`, run `bench clear-cache`                    |
| Live updates broken | Check `redis_socketio` and socketio process                     |


---

## Tips

- Keep Redis and the app in the **same region/network** if possible
- Set `maxmemory` so Redis does not use all RAM
- Use a password in production (`use_redis_auth: true`)

---

