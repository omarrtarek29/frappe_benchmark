# Frappe Benchmark

A generic benchmark toolkit for stress-testing any Frappe/ERPNext deployment (v15+) with millions of synthetic records.

## Features

- **High-throughput data generation**: Generate millions of realistic-looking records using Faker and bulk inserts
- **Parallel processing**: Split large generation jobs across multiple RQ workers
- **Performance benchmarks**: 15 timed queries measuring aggregation, join, and filter performance
- **Interactive reports**: Desk-based Query Reports for manual stress testing
- **Version compatible**: Works with Frappe v15 and v16

## Infrastructure Guides (Multi-Server Setup)

Simple step-by-step guides for running Frappe on separate servers:

- [docs/01-redis-decoupling-guide.md](docs/01-redis-decoupling-guide.md) — when and how to move Redis off the app server
- [docs/02-database-decoupling-guide.md](docs/02-database-decoupling-guide.md) — when and how to move MariaDB off the app server

## Installation

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app https://github.com/YOUR_REPO/frappe_benchmark --branch main
bench --site YOUR_SITE install-app frappe_benchmark
```

After installation:

```bash
bench --site YOUR_SITE migrate
bench pip install faker
bench build --app frappe_benchmark
sudo supervisorctl restart all
```

## Commands

### Generate Data

```bash
# Basic usage - 10k customers, 5k items, 100k invoices
bench --site YOUR_SITE generate-benchmark-data

# Scale up for serious testing
bench --site YOUR_SITE generate-benchmark-data \
    --customers 50000 \
    --items 20000 \
    --invoices 10000000 \
    --items-per-invoice 4 \
    --workers 8

# Fast load mode (drops indexes during load)
bench --site YOUR_SITE generate-benchmark-data \
    --invoices 5000000 \
    --fast-load \
    --workers 8

# Run synchronously (no background jobs)
bench --site YOUR_SITE generate-benchmark-data --inline
```

**Options:**


| Option                | Default | Description                             |
| --------------------- | ------- | --------------------------------------- |
| `--customers`         | 10,000  | Number of customers to generate         |
| `--items`             | 5,000   | Number of items to generate             |
| `--invoices`          | 100,000 | Number of invoices to generate          |
| `--items-per-invoice` | 3       | Average line items per invoice          |
| `--workers`           | 4       | Parallel RQ workers for invoices        |
| `--inline`            | false   | Run synchronously (no background jobs)  |
| `--fast-load`         | false   | Drop indexes before load, rebuild after |
| `--clear-first`       | false   | Delete existing data before generating  |


### Run Benchmark Report

```bash
# Run queries and print results
bench --site YOUR_SITE benchmark-report

# Save results to Benchmark Run doctype for historical comparison
bench --site YOUR_SITE benchmark-report --save
```

### Check Status

```bash
bench --site YOUR_SITE benchmark-status
```

### Clear All Data

```bash
bench --site YOUR_SITE clear-benchmark-data --yes
```

## DocTypes


| DocType                      | Purpose                                                 |
| ---------------------------- | ------------------------------------------------------- |
| Benchmark Customer           | Synthetic customers with territory, group, credit limit |
| Benchmark Item               | Products with item groups, brands, standard rates       |
| Benchmark Sales Invoice      | Transactions with child line items, status tracking     |
| Benchmark Sales Invoice Item | Child table for invoice line items                      |
| Benchmark Run                | Stores benchmark timing results for comparison          |


## Query Reports

Access via Desk > Benchmark module:

- **Benchmark Revenue Summary**: Revenue by territory/month/status
- **Benchmark Customer Activity**: Customer metrics with invoice stats

## Performance Tips

1. **Use `--fast-load`** for >1M records - drops indexes during load
2. **Increase `--workers`** based on available RQ workers
3. **Monitor jobs**: `bench --site <site> show-pending-jobs`
4. **Remote DB**: Network latency affects bulk insert; use larger batch sizes

## Expected Scale

- 10M+ invoices with 30-40M line items
- Generation rate: ~10-50k invoices/minute per worker
- Benchmark queries work on 100M+ row tables

## Benchmark Queries (15 total)

1. Total record counts
2. Revenue by month (60 months)
3. Revenue by territory
4. Revenue by customer group (join)
5. Top 100 customers by revenue
6. Top 100 customers by outstanding
7. Invoice status distribution
8. Top 100 items by quantity
9. Average items per invoice
10. Invoices last 12 months (date index test)
11. Filtered by status + territory (compound index test)
12. Paginated list simulation
13. Invoice + items join (30 days)
14. Customer invoice summary (top 500)
15. Monthly trend analysis (3 years)

## License

MIT