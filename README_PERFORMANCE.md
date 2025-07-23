# Performance Configuration

## Health Checks

By default, the graceful fetcher runs **without health checks** for maximum speed. Health checks are disabled by default to provide faster execution.

### Running without health checks (default - fast mode):
```bash
# Just run normally
python src/graceful_fetcher.py

# Or use the convenience script
./run_fast.sh
```

### Running with health checks enabled:
```bash
# Enable health monitoring
ENABLE_RPC_MONITORING=true python src/graceful_fetcher.py

# Or use the convenience script
./run_with_health_checks.sh
```

## What changes with health checks?

**Without health checks (default):**
- Uses configured RPC URLs directly
- Only uses first 3 fallback URLs for speed
- No endpoint health monitoring
- Faster execution (~2-5 minutes)

**With health checks enabled:**
- Tests all RPC endpoints before use
- Skips unhealthy networks
- Uses all available fallback URLs
- Provides detailed health reports
- Slower execution (~10-15 minutes)

## When to use health checks?

- **Production monitoring**: Enable health checks for production runs where reliability is critical
- **Development/Testing**: Keep health checks disabled for faster iteration
- **Debugging RPC issues**: Enable health checks to diagnose endpoint problems