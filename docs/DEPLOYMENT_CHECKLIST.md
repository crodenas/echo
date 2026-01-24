# ECHO Deployment Checklist

This checklist ensures safe deployment of the enhanced ECHO system with environment-based configuration, comprehensive error handling, and AWS integration improvements.

## Pre-Deployment

### 1. Environment Setup

- [ ] **Copy environment template**
  ```bash
  cp .env.example .env
  ```

- [ ] **Configure AWS credentials**
  - Set up AWS credentials file (`~/.aws/credentials`) or use IAM role
  - Verify credentials with: `aws sts get-caller-identity`

- [ ] **Update .env file with actual values**
  - Replace `{ACCOUNT_ID}` with your AWS account ID
  - Replace `{RANDOM_ID}` in execution role ARN with actual role ID
  - Verify queue names match your CloudFormation stack outputs
  - Set appropriate log level (DEBUG for initial deployment, INFO for production)

- [ ] **Validate .env configuration**
  ```bash
  # Ensure .env is not in version control
  git check-ignore .env  # Should output: .env

  # Verify all required variables are set
  grep -E "AWS_|DATABASE_|LOG_LEVEL" .env
  ```

### 2. Dependencies

- [ ] **Install/update dependencies**
  ```bash
  uv sync
  ```

- [ ] **Verify new dependencies installed**
  ```bash
  uv pip list | grep -E "pydantic-settings|tenacity|moto"
  ```

### 3. Database Preparation

- [ ] **Backup existing database** (if applicable)
  ```bash
  cp src/data/echo.db src/data/echo.db.backup.$(date +%Y%m%d_%H%M%S)
  ```

- [ ] **Verify database directory permissions**
  ```bash
  ls -la src/data/
  ```

### 4. Code Verification

- [ ] **Verify no hardcoded credentials in source**
  ```bash
  grep -r "891242332196" src/ --exclude-dir=__pycache__ || echo "✓ Clean"
  grep -r "arn:aws:iam::" src/ --exclude-dir=__pycache__ | grep -v ".env" || echo "✓ Clean"
  ```

- [ ] **Clean Python bytecode cache**
  ```bash
  find src/ -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
  find src/ -type f -name "*.pyc" -delete
  ```

- [ ] **Run linting** (optional but recommended)
  ```bash
  uv run isort src/
  uv run pylint src/ || true  # Don't fail on warnings
  ```

## Deployment

### 5. Pre-Deployment Testing

- [ ] **Run existing tests**
  ```bash
  uv run pytest
  ```

- [ ] **Validate settings load correctly**
  ```bash
  uv run python -c "from core.settings import get_settings; s = get_settings(); print(f'✓ Settings loaded: {s.aws.region}')"
  ```

- [ ] **Test AWS connectivity** (dry run)
  ```bash
  aws scheduler list-schedule-groups --max-results 1
  aws sqs get-queue-attributes --queue-url $(grep AWS_QUEUE_1_URL .env | cut -d= -f2)
  ```

### 6. Application Startup

- [ ] **Start application in development mode**
  ```bash
  uv run fastapi dev src/main.py
  ```

- [ ] **Monitor startup logs for errors**
  - Look for "AWS connectivity validation successful"
  - Look for "SQS consumers started successfully"
  - Verify no credential errors or configuration errors

- [ ] **Verify API is responsive**
  ```bash
  curl http://localhost:8000/
  curl http://localhost:8000/api/campaigns
  ```

### 7. Functional Testing

- [ ] **Create a test campaign**
  ```bash
  curl -X POST http://localhost:8000/api/campaigns \
    -H "Content-Type: application/json" \
    -d '{
      "name": "Test Campaign",
      "description": "Deployment verification test",
      "campaign_schedule": "cron(0 12 * * ? *)",
      "cycle_schedule": "cron(0 * * * ? *)",
      "max_events": 3,
      "conn_string": "test://localhost"
    }'
  ```

- [ ] **Verify AWS resources created**
  ```bash
  # Get campaign ID from response above
  CAMPAIGN_ID=<campaign_id>

  # Verify schedule group exists
  aws scheduler list-schedule-groups | grep "campaign_${CAMPAIGN_ID}_group"

  # Verify campaign schedule exists
  aws scheduler get-schedule \
    --name "campaign_${CAMPAIGN_ID}_schedule" \
    --group-name "campaign_${CAMPAIGN_ID}_group"
  ```

- [ ] **Test campaign retrieval**
  ```bash
  curl http://localhost:8000/api/campaigns/$CAMPAIGN_ID
  ```

- [ ] **Test campaign update**
  ```bash
  curl -X PUT http://localhost:8000/api/campaigns/$CAMPAIGN_ID \
    -H "Content-Type: application/json" \
    -d '{
      "id": '$CAMPAIGN_ID',
      "name": "Updated Test Campaign",
      "description": "Updated description",
      "campaign_schedule": "cron(0 13 * * ? *)",
      "cycle_schedule": "cron(0 * * * ? *)",
      "max_events": 3,
      "conn_string": "test://localhost"
    }'
  ```

- [ ] **Test campaign deletion**
  ```bash
  curl -X DELETE http://localhost:8000/api/campaigns/$CAMPAIGN_ID

  # Verify schedule group deleted
  aws scheduler list-schedule-groups | grep "campaign_${CAMPAIGN_ID}_group" || echo "✓ Deleted"
  ```

### 8. Error Handling Verification

- [ ] **Test invalid configuration** (optional)
  - Temporarily modify .env with invalid queue URL
  - Restart application
  - Verify application fails fast with clear error message
  - Restore valid .env

- [ ] **Test AWS throttling resilience** (if possible)
  - Create multiple campaigns rapidly
  - Verify retry logic activates
  - Check logs for retry attempts

- [ ] **Verify logging levels**
  ```bash
  # Test different log levels
  LOG_LEVEL=DEBUG uv run fastapi dev src/main.py  # Should see debug logs
  LOG_LEVEL=WARNING uv run fastapi dev src/main.py  # Should see fewer logs
  ```

## Post-Deployment

### 9. Monitoring Setup

- [ ] **Configure log aggregation** (if applicable)
  - Point log aggregator to application logs
  - Set up alerts for CRITICAL and ERROR level logs

- [ ] **Set up AWS CloudWatch monitoring** (recommended)
  - Monitor EventBridge Scheduler invocation counts
  - Monitor SQS queue depths
  - Set up alarms for:
    - High SQS message age (> 5 minutes)
    - High DLQ message count
    - EventBridge Scheduler failures

- [ ] **Document deployment**
  - Record deployment time
  - Note any issues encountered
  - Update team documentation with new .env requirements

### 10. Production Deployment

For production environments, additionally:

- [ ] **Use production-grade secrets management**
  - Use AWS Secrets Manager, Parameter Store, or equivalent
  - Never use .env files in production servers
  - Use IAM roles instead of access keys when possible

- [ ] **Set appropriate log level**
  - Use `LOG_LEVEL=INFO` or `LOG_LEVEL=WARNING` in production
  - Never use `DEBUG` in production (performance impact)

- [ ] **Configure retry limits for production**
  - Review `AWS_MAX_RETRY_ATTEMPTS` in .env
  - Adjust based on expected AWS throttling rates

- [ ] **Set up automated backups**
  - Database backups (if using persistent storage)
  - Configuration backups

- [ ] **Load testing** (recommended)
  - Test campaign creation under load
  - Verify queue consumer performance
  - Validate retry behavior under stress

## Rollback Plan

If deployment fails:

1. **Stop the application**
   ```bash
   # Ctrl+C or kill the process
   ```

2. **Restore previous configuration**
   ```bash
   git checkout HEAD -- src/
   ```

3. **Restore database backup** (if needed)
   ```bash
   cp src/data/echo.db.backup.YYYYMMDD_HHMMSS src/data/echo.db
   ```

4. **Clean up orphaned AWS resources**
   ```bash
   # List all schedule groups
   aws scheduler list-schedule-groups

   # Delete orphaned groups manually
   aws scheduler delete-schedule-group --name <group-name>
   ```

5. **Review logs for root cause**
   ```bash
   tail -n 100 <log-file>
   ```

6. **Report issues**
   - Document the failure
   - Create issue in GitHub repository
   - Include relevant log excerpts

## Success Criteria

Deployment is successful when:

- [X] Application starts without errors
- [X] AWS connectivity validation passes
- [X] SQS consumers start successfully
- [X] Campaign CRUD operations work correctly
- [X] AWS schedules created/updated/deleted as expected
- [X] No hardcoded credentials in source code
- [X] Logs show appropriate level of detail
- [X] Error handling works (retries, timeouts, etc.)
- [X] All existing tests pass

## Security Checklist

- [X] `.env` file excluded from version control
- [X] No AWS credentials committed to repository
- [X] `.env.example` contains only placeholders
- [X] Python bytecode cache cleaned
- [X] IAM execution role has minimum required permissions
- [X] SQS queues have appropriate access policies
- [X] EventBridge Scheduler execution role properly scoped

## Support

If issues arise during deployment:

1. Check application logs for detailed error messages
2. Verify AWS credentials: `aws sts get-caller-identity`
3. Verify queue URLs: `aws sqs get-queue-attributes --queue-url <url>`
4. Review `.env` file for typos or missing values
5. Consult README.md for configuration details
6. Create an issue at: https://github.com/anthropics/claude-code/issues (placeholder)
