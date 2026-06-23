# MariaDB on a Separate Server

Move Frappe's database off the app server onto its own machine.

---

## Your servers (example IPs)


| Server   | IP               | What runs there           |
| -------- | ---------------- | ------------------------- |
| App      | `95.xxx.xxx.222` | Frappe, Gunicorn, workers |
| Redis    | `95.xxx.xxx.223` | Redis (see other guide)   |
| Database | `95.xxx.xxx.224` | MariaDB only              |


On the app server, set in `sites/common_site_config.json`:

```json
{
  "db_host": "95.xxx.xxx.224"
}
```

User, password, and database name stay in `sites/YOUR_SITE/site_config.json`.  
Do not put passwords in git.

---

## Do I need a separate database server?

**Yes, if you see:**

- Server runs out of **RAM** or uses **swap** all the time
- Site is **slow during backups** or `bench migrate`
- **Disk is always busy** (`iostat` shows high usage during normal use)
- You need more app workers but **cannot give MariaDB more memory** on the same box
- Compliance requires the database on its own server

**No, if:**

- Site is fast enough for your users
- Backups and updates can run without hurting daily use
- One server has enough RAM for Frappe + MariaDB

**Simple rule:** If your database (plus indexes) needs more than about **half the server's RAM**, and Frappe also needs RAM, consider a dedicated DB server. Row counts alone do not tell you — a small database with heavy reports can still need a split.

---

## Why bother?

1. **Give MariaDB most of the RAM** — queries run from memory, not disk
2. **Disk is for the database only** — backups and imports do not slow the website as much
3. **Scale app and DB separately** — add web workers without shrinking the database cache

---

## Step 1 — Set up the database server (`95.xxx.xxx.224`)

### Allow connections from the app server

```bash
sudo nano /etc/mysql/mariadb.conf.d/50-server.cnf
```

Set:

```ini
bind-address = 0.0.0.0
```

### Tune memory (example for a 12 GB server)

Add or edit in the same folder (e.g. `99-frappe.cnf`):

```ini
[mysqld]
innodb_buffer_pool_size = 8G
innodb_log_file_size = 2G
max_connections = 500
```

Restart:

```bash
sudo systemctl restart mariadb
```

### Create database user for the app server

On the **DB server**:

```bash
sudo mysql -u root -p
```

```sql
CREATE USER IF NOT EXISTS '_YOUR_DB_USER'@'95.xxx.xxx.222' IDENTIFIED BY 'YOUR_PASSWORD';
GRANT ALL PRIVILEGES ON `_YOUR_DB_NAME`.* TO '_YOUR_DB_USER'@'95.xxx.xxx.222';
FLUSH PRIVILEGES;
EXIT;
```

Replace `_YOUR_DB_USER`, `_YOUR_DB_NAME`, and `YOUR_PASSWORD` from your site's `site_config.json`.

### Firewall — only allow the app server

```bash
sudo ufw allow ssh
sudo ufw allow from 95.xxx.xxx.222 to any port 3306 proto tcp
sudo ufw enable
```

Also allow port **3306 from the app IP only** in your cloud firewall.  
Never open 3306 to the whole internet.

---

## Step 2 — Point Frappe at the database (`95.xxx.xxx.222`)

Edit `sites/common_site_config.json`:

```json
{
  "db_host": "95.xxx.xxx.224"
}
```

Test:

```bash
bench --site YOUR_SITE mariadb
```

If you get a MariaDB prompt, it works.

Restart Frappe:

```bash
bench clear-cache
bench restart
```

---

## Slow reports or list views?

Large tables need **indexes**. After schema changes:

```bash
bench --site YOUR_SITE migrate
```

Check indexes on your busiest tables:

```sql
SHOW INDEX FROM `tabSales Invoice` \G
SHOW INDEX FROM `tabSales Invoice Item` \G
```

If list views are still slow, ask which fields you filter on — those fields usually need an index.

---

## Common problems


| Problem                | Fix                                                                 |
| ---------------------- | ------------------------------------------------------------------- |
| Can't connect to MySQL | Firewall, `bind-address = 0.0.0.0`, correct `db_host`               |
| Access denied          | Re-run GRANT for user `@'95.xxx.xxx.222'`                           |
| Migrate takes forever  | Normal on huge tables — wait, check `SHOW PROCESSLIST` on DB server |
| Reports very slow      | Run `bench migrate`, check indexes                                  |
| DB server CPU at 100%  | Increase `innodb_buffer_pool_size` if RAM allows                    |


### Error: `MAX_JOIN_SIZE` when querying huge tables

```sql
SET SESSION SQL_BIG_SELECTS=1;
SELECT * FROM `tabYour DocType` LIMIT 10;
```

Always use `LIMIT` when exploring big tables in the SQL console.

---

## Using frappe_benchmark on this setup

If you use this app to load test:

- After `--fast-load`, run `bench migrate` to restore indexes
- Run `bench --site YOUR_SITE benchmark-report --tier quick` to measure query speed

Details: [README.md](../README.md)

---

## Tips

- Use a **private network** between app and DB when possible
- Run heavy `bench migrate` jobs in a **maintenance window**
- Back up from the DB server with `mariadb-dump`, not through the app

---

