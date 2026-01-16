# UITTREKSEL (EXTRACT) - MAXIMAAL 250 WOORDEN

## Intelligent Database Scanner - Multi-Engine PII Detection

---

## TITEL

Intelligent Database Scanner with Multi-Engine Support (PostgreSQL, MySQL, MongoDB, Redis, SQLite, MSSQL), Priority-Based Table Selection, Adaptive Sampling Strategies, and Netherlands BSN Detection

---

## SAMENVATTING (248 WOORDEN)

Een intelligent database scanning systeem voor PII detection across multiple database engines. De uitvinding ondersteunt 6 database types via unified connection abstraction: PostgreSQL (psycopg2), MySQL (mysql.connector), MongoDB (pymongo), Redis (redis-py), SQLite (sqlite3), Microsoft SQL Server (pyodbc).

Priority-based table selection algorithm implementeert scoring: user/customer/employee 3.0× (hoogste prioriteit), medical/health/patient 3.0×, payment/billing 2.8×, transaction 2.5×, contact/address/phone/email 2.5×, financial/bank 2.8×, credential/password 2.8×, session 2.0×, audit/log 1.5×, system 1.2×, temp/test 0.5-0.8× (laagste). Table priority calculation: base_score + column_boost, capped at 3.5.

Adaptive sampling strategies met 3 modes: fast (100 rows/table, 2 workers, ≤15 tables), smart (300 rows/table, 3 workers, ≤50 tables), deep (500 rows/table, 3 workers, ≤75 tables). Strategy selection gebaseerd op total_tables, estimated_rows, risk_level parameters.

Parallel scanning engine met ThreadPoolExecutor (3 concurrent workers) reducing scan time 60% (4 hours → 1.6 hours). Connection pooling per worker thread met timeout=60 seconds per table scan.

**Netherlands specialization**: BSN detection met 11-proef checksum validation: (d₀×9 + d₁×8 + d₂×7 + d₃×6 + d₄×5 + d₅×4 + d₆×3 + d₇×2 - d₈×1) mod 11 == 0. Additional Netherlands patterns: IBAN NL (NL\d{2}[A-Z]{4}\d{10}), KvK 8-digit numbers, Dutch postal codes (1234AB), Dutch phone numbers (+31).

Schema intelligence analyzer berekent risk_level: high (risk_score > 10), medium (risk_score > 5), low (risk_score ≤ 5), waar risk_score = (high_priority_tables × 3) + (medium_priority_tables × 1.5). Scan coverage metrics: (tables_scanned / tables_discovered) × 100.

Competitor gap: OneTrust/TrustArc support only 2-3 engines, lack MongoDB/Redis, no parallel scanning, no BSN checksum validation.

**[WOORDEN TELLING: 248/250]**

---

**EINDE UITTREKSEL**
