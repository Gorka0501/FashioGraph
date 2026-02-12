# Administration Guide - Backup & Recovery

Backup strategies and disaster recovery procedures.

## Backup Overview

### Backup Components

1. **Database** - User data, wardrobes, items, outfits
2. **User Files** - Uploaded images and documents
3. **Configuration** - Environment variables, SSL certificates
4. **Models** - Trained personal models

### Recovery Time Objectives (RTO)

- **Critical Systems:** < 1 hour
- **User Data:** < 4 hours
- **Models:** < 24 hours

---

## Database Backups

### SQLite Backup

```bash
# Full backup (simple copy)
cp app.db app.db.backup.$(date +%Y%m%d_%H%M%S)

# Compressed backup
sqlite3 app.db ".dump" | gzip > app.db.backup.$(date +%Y%m%d_%H%M%S).sql.gz

# Restore from backup
gunzip < app.db.backup.20240115_120000.sql.gz | sqlite3 app.db.restored
```

### PostgreSQL Backup

```bash
# Full database backup
pg_dump -h localhost -U fashion fashion_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Compressed backup
pg_dump -h localhost -U fashion fashion_db | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz

# Custom format (more efficient)
pg_dump -h localhost -U fashion -Fc fashion_db > backup_$(date +%Y%m%d_%H%M%S).dump

# Parallel backup (faster for large databases)
pg_dump -h localhost -U fashion -j 4 -Fc fashion_db > backup.dump
```

### PostgreSQL Restore

```bash
# From SQL backup
psql -h localhost -U fashion fashion_db < backup.sql

# From compressed backup
gunzip < backup.sql.gz | psql -h localhost -U fashion fashion_db

# From custom format
pg_restore -h localhost -U fashion -d fashion_db backup.dump
```

### Automated Database Backups

**File:** `backup_database.sh`

```bash
#!/bin/bash
set -e

# Configuration
BACKUP_DIR="/mnt/backups/database"
RETENTION_DAYS=30
DB_NAME="fashion_db"
DB_USER="fashion"
DB_HOST="localhost"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Generate backup filename
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_$BACKUP_DATE.sql.gz"

# Perform backup
echo "Starting database backup..."
pg_dump -h "$DB_HOST" -U "$DB_USER" "$DB_NAME" | gzip > "$BACKUP_FILE"

# Verify backup
if gzip -t "$BACKUP_FILE" 2>/dev/null; then
    echo "Backup successful: $BACKUP_FILE"
    
    # Log backup
    echo "$(date): Backup successful - $BACKUP_FILE" >> "$BACKUP_DIR/backup.log"
else
    echo "Backup verification failed!"
    exit 1
fi

# Delete old backups
echo "Removing backups older than $RETENTION_DAYS days..."
find "$BACKUP_DIR" -name "backup_*.sql.gz" -mtime "+$RETENTION_DAYS" -delete

# Send notification
echo "Backup completed successfully" | mail -s "Database Backup Report" ops@example.com
```

### Cron Job for Automated Backups

```bash
# Daily backup at 2 AM
0 2 * * * /usr/local/bin/backup_database.sh

# Weekly backup on Sunday
0 3 * * 0 /usr/local/bin/backup_database.sh

# Schedule with email notification
0 2 * * * /usr/local/bin/backup_database.sh 2>&1 | mail -s "Backup Report" ops@example.com
```

---

## File Backups

### User Images Backup

```bash
# Configuration
SOURCE_DIR="$HOME/.fashion_wardrobe_app/images"
BACKUP_DIR="/mnt/backups/images"
RETENTION_DAYS=30

# Full backup
tar -czf "$BACKUP_DIR/images_$(date +%Y%m%d_%H%M%S).tar.gz" "$SOURCE_DIR"

# Incremental backup (files modified in last day)
find "$SOURCE_DIR" -type f -mtime -1 | tar -czf "$BACKUP_DIR/images_incremental_$(date +%Y%m%d_%H%M%S).tar.gz" -T -

# Delete old backups
find "$BACKUP_DIR" -name "images_*.tar.gz" -mtime "+$RETENTION_DAYS" -delete
```

### Model Backups

```bash
# Backup trained models
SOURCE_DIR="$HOME/.fashion_wardrobe_app/models"
BACKUP_DIR="/mnt/backups/models"

# Backup all models
tar -czf "$BACKUP_DIR/models_$(date +%Y%m%d_%H%M%S).tar.gz" "$SOURCE_DIR"

# List backed up models
tar -tzf models_backup.tar.gz | head -20
```

---

## Cloud Backups

### AWS S3 Backup

```bash
# Configuration
BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).sql.gz"
S3_BUCKET="fashion-app-backups"
S3_PREFIX="database/"

# Backup to S3
pg_dump -U fashion fashion_db | gzip | \
  aws s3 cp - "s3://$S3_BUCKET/$S3_PREFIX$BACKUP_FILE" \
  --sse AES256 \
  --storage-class GLACIER

# List backups in S3
aws s3 ls "s3://$S3_BUCKET/$S3_PREFIX" --recursive

# Restore from S3
aws s3 cp "s3://$S3_BUCKET/$S3_PREFIX$BACKUP_FILE" - | \
  gunzip | psql -U fashion fashion_db
```

### Configure AWS Backup

```bash
# Install AWS CLI
pip install awscli

# Configure credentials
aws configure

# Test access
aws s3 ls
```

### Backblaze B2 Backup

```bash
# Install Backblaze CLI
pip install b2

# Authenticate
b2 authorize-account <application_key_id> <application_key>

# Upload backup
b2 upload-file \
  <bucket_id> \
  backup_database.sql.gz \
  database/backup_$(date +%Y%m%d_%H%M%S).sql.gz

# List backups
b2 list-file-names <bucket_id> database/
```

---

## Backup Verification

### Verify Database Backup

```bash
# Test restore without modifying original
createdb -U fashion fashion_db_test
gunzip < backup.sql.gz | psql -U fashion fashion_db_test

# Verify data
psql -U fashion -d fashion_db_test -c "SELECT COUNT(*) FROM users;"

# Drop test database
dropdb -U fashion fashion_db_test
```

### Verify File Backup

```bash
# List backup contents
tar -tzf images_backup.tar.gz | head -20

# Extract to test location
mkdir -p /tmp/backup_test
tar -xzf images_backup.tar.gz -C /tmp/backup_test

# Compare file count
echo "Original files: $(find ~/.fashion_wardrobe_app/images -type f | wc -l)"
echo "Backup files: $(find /tmp/backup_test -type f | wc -l)"

# Cleanup
rm -rf /tmp/backup_test
```

---

## Disaster Recovery Plan

### Step 1: Assess Damage

```bash
# Check system status
systemctl status fashion-app

# Check database
pg_isready -h localhost -U fashion

# Check disk space
df -h /

# Check files
ls -la ~/.fashion_wardrobe_app/
```

### Step 2: Stop Application

```bash
# Stop application
sudo systemctl stop fashion-app

# Stop database (if needed)
sudo systemctl stop postgresql
```

### Step 3: Restore Database

```bash
# Get latest backup
LATEST_BACKUP=$(ls -t /mnt/backups/database/backup_*.sql.gz | head -1)

# Create new database
createdb -U fashion fashion_db_new

# Restore backup
gunzip < "$LATEST_BACKUP" | psql -U fashion fashion_db_new

# Rename old database (keep for safety)
psql -U fashion -c "ALTER DATABASE fashion_db RENAME TO fashion_db_old;"
psql -U fashion -c "ALTER DATABASE fashion_db_new RENAME TO fashion_db;"
```

### Step 4: Restore Files

```bash
# Get latest backup
LATEST_BACKUP=$(ls -t /mnt/backups/images/images_*.tar.gz | head -1)

# Create temporary directory
mkdir -p /tmp/restore

# Extract backup
tar -xzf "$LATEST_BACKUP" -C /tmp/restore

# Copy to application directory
cp -r /tmp/restore/home/user/.fashion_wardrobe_app/images/* \
      ~/.fashion_wardrobe_app/images/

# Fix permissions
chown -R fashion:fashion ~/.fashion_wardrobe_app/

# Cleanup
rm -rf /tmp/restore
```

### Step 5: Verify & Restart

```bash
# Verify database
psql -U fashion -d fashion_db -c "SELECT COUNT(*) FROM users;"

# Verify files
ls -la ~/.fashion_wardrobe_app/images/ | head -10

# Start application
sudo systemctl start fashion-app

# Verify application
curl http://localhost:8000/health
```

---

## Backup Monitoring

### Backup Status Check

```bash
#!/bin/bash

BACKUP_DIR="/mnt/backups/database"
ALERT_EMAIL="ops@example.com"

# Check if backup exists
LATEST_BACKUP=$(ls -t "$BACKUP_DIR/backup_"*.sql.gz 2>/dev/null | head -1)

if [ -z "$LATEST_BACKUP" ]; then
    echo "ERROR: No backup found!" | mail -s "Backup Alert" "$ALERT_EMAIL"
    exit 1
fi

# Check backup age
BACKUP_AGE=$(($(date +%s) - $(stat -c %Y "$LATEST_BACKUP")))
MAX_AGE=$((36 * 3600))  # 36 hours

if [ $BACKUP_AGE -gt $MAX_AGE ]; then
    echo "ERROR: Backup is older than 36 hours!" | mail -s "Backup Alert" "$ALERT_EMAIL"
    exit 1
fi

# Check backup size
BACKUP_SIZE=$(stat -c %s "$LATEST_BACKUP")
MIN_SIZE=$((1 * 1024 * 1024))  # 1 MB minimum

if [ $BACKUP_SIZE -lt $MIN_SIZE ]; then
    echo "ERROR: Backup size is suspiciously small!" | mail -s "Backup Alert" "$ALERT_EMAIL"
    exit 1
fi

echo "Backup status: OK"
echo "Latest backup: $LATEST_BACKUP ($(numfmt --to=iec $BACKUP_SIZE))"
```

### Schedule Backup Monitor

```bash
# Run every 6 hours
0 */6 * * * /usr/local/bin/check_backup_status.sh
```

---

## Backup Best Practices

| Practice | Description |
|----------|-------------|
| **3-2-1 Rule** | 3 copies, 2 different media, 1 offsite |
| **Frequency** | Daily for critical data, weekly for archives |
| **Testing** | Test restore at least monthly |
| **Encryption** | Encrypt backups in transit and at rest |
| **Documentation** | Document recovery procedures |
| **Automation** | Automate backup and verification |
| **Retention** | Keep daily for 7 days, weekly for 4 weeks |
| **Monitoring** | Alert on failed backups |

---

## Recovery Scenarios

### Scenario 1: Database Corruption

```bash
# Detect corruption
PGPASSWORD=password pg_dump -h localhost -U fashion fashion_db > /dev/null

# Restore from backup
gunzip < /mnt/backups/database/backup_latest.sql.gz | psql -U fashion -d fashion_db_new

# Switch databases
psql -U fashion -c "ALTER DATABASE fashion_db RENAME TO fashion_db_corrupted;"
psql -U fashion -c "ALTER DATABASE fashion_db_new RENAME TO fashion_db;"
```

### Scenario 2: Accidental Data Deletion

```bash
# Query backup to find deleted record
psql -h localhost -U fashion -d fashion_db_restored \
  -c "SELECT * FROM wardrobes WHERE id = 123;"

# Restore specific record
pg_dump -h localhost -U fashion fashion_db_restored --table=wardrobes | \
  psql -U fashion -d fashion_db
```

### Scenario 3: File System Failure

```bash
# Restore all images
tar -xzf /mnt/backups/images/images_latest.tar.gz \
  -C ~/.fashion_wardrobe_app/ \
  --strip-components=5

# Verify restore
find ~/.fashion_wardrobe_app/images -type f | wc -l
```

---

## Disaster Recovery Checklist

- [ ] Backup location documented
- [ ] Backup access credentials secured
- [ ] Recovery procedures documented
- [ ] Team trained on recovery
- [ ] Backup tested monthly
- [ ] RTO/RPO defined
- [ ] Backup monitoring alerts configured
- [ ] Off-site backup configured
- [ ] Backup encryption enabled
- [ ] Emergency contact list updated

---

## Next Steps

- Review [Security Guide](security.md)
- Check [Monitoring Guide](monitoring.md)
- Read [Deployment Guide](deployment.md)
