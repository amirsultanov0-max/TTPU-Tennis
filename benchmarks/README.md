# Database Benchmarks

These scripts were used during development to investigate
PostgreSQL / Supabase database connection and query latency.

They are development and diagnostic tools only.
They are not required to run the Telegram bot.

The benchmarks cover:

- asyncpg connection latency
- connection reuse
- SQLAlchemy connection pooling
- database query latency
- combined database operations
- direct PostgreSQL connection testing