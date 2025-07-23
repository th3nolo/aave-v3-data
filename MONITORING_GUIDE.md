# Monitoring and Debugging Guide

This guide covers the comprehensive monitoring and debugging features implemented in the Aave V3 Data Fetcher.

## Overview

The monitoring system provides:
- **Comprehensive logging** throughout the fetcher script
- **Error reporting and debugging output** with detailed context
- **Performance monitoring** for RPC call timing and network operations
- **Data freshness validation** to ensure data quality
- **Health monitoring** for RPC endpoints and network status

## Features

### 1. Comprehensive Logging

The system uses Python's logging module with structured, timestamped logs:

```bash
# Enable debug logging
python aave_fetcher.py --debug

# Save logs to file
python aave_fetcher.py --log-file fetcher.log

# Both debug and file logging
python aave_fetcher.py --debug --log-file fetcher.log
```

**Log Levels:**
- `DEBUG`: Detailed operation information, RPC calls, asset processing
- `INFO`: General progress, network completion, summary statistics
- `WARNING`: Non-critical issues, slow responses, low success rates
- `ERROR`: Failed operations, critical errors

### 2. Performance Monitoring

#### RPC Call Monitoring
- Tracks individual RPC call timing and success rates
- Records response sizes and retry attempts
- Identifies slow or failing endpoints

#### Network Performance Metrics
- Processing time per network
- Assets processed per network
- RPC call statistics and success rates
- Average response times

#### Performance Profiling
- Operation-level timing with context managers
- Statistical analysis of operation performance
- Identification of bottlenecks

```bash
# Save detailed performance report
python aave_fetcher.py --save-performance-report

# View performance summary in console
python aave_fetcher.py --debug
```

### 3. Error Reporting and Debugging

#### Debug Reports
Comprehensive debug reports include:
- Network health status
- Performance metrics
- RPC call history (optional)
- Error and warning summaries
- Endpoint health details

```bash
# Save debug report
python aave_fetcher.py --save-debug-report

# Include full RPC call history
python aave_fetcher.py --save-debug-report --include-rpc-history
```

#### Error Context
- Detailed error messages with network context
- RPC failure analysis with retry information
- Asset processing error tracking
- Network-specific error aggregation

### 4. Data Freshness Validation

Validates the freshness of fetched data by checking timestamps:

```bash
# Enable data freshness validation
python aave_fetcher.py --validate-freshness
```

**Validation Checks:**
- Timestamp presence and validity
- Data age against freshness threshold (2 hours default)
- Network-level freshness scoring
- Stale data identification and reporting

### 5. Health Monitoring

#### Endpoint Health Checks
- Response time monitoring
- Consecutive failure tracking
- Automatic failover to backup endpoints
- Health status reporting

#### Network Health Assessment
- Overall network status (healthy/degraded/unhealthy)
- Primary and fallback endpoint status
- Success rate tracking
- Last successful call timestamps

## Command Line Options

### Basic Monitoring
```bash
--debug                    # Enable debug logging
--log-file LOG_FILE       # Save logs to file
--validate-freshness      # Validate data timestamps
```

### Advanced Reporting
```bash
--save-debug-report       # Save comprehensive debug report
--save-performance-report # Save detailed performance metrics
--include-rpc-history     # Include RPC call history in debug report
```

### Standard Options
```bash
--skip-reports            # Skip saving health/fetch reports
--timeout TIMEOUT         # Timeout per network in seconds
```

## Output Files

### Performance Report (`performance_report.json`)
```json
{
  "timestamp": "2025-01-15T10:30:00",
  "profiler_stats": {
    "fetch_network_ethereum": {
      "count": 1,
      "total_time": 45.2,
      "average_time": 45.2,
      "min_time": 45.2,
      "max_time": 45.2
    }
  },
  "network_metrics": {
    "ethereum": {
      "network_name": "Ethereum Mainnet",
      "duration": 45.2,
      "assets_processed": 25,
      "rpc_calls": 52,
      "successful_calls": 50,
      "failed_calls": 2,
      "success_rate": 0.96,
      "average_rpc_time": 0.85,
      "total_response_size": 125000,
      "errors": ["getReserveData: Connection timeout"],
      "warnings": []
    }
  },
  "overall_stats": {
    "total_networks": 13,
    "total_rpc_calls": 650,
    "total_successful_calls": 625,
    "total_failed_calls": 25,
    "total_assets_processed": 320,
    "average_network_time": 35.5,
    "average_rpc_time": 0.75
  }
}
```

### Debug Report (`debug_report.json`)
Includes all performance data plus:
- Detailed endpoint health information
- Complete RPC call history (if enabled)
- Network health summaries
- Error and warning details

### Freshness Report (`freshness_report.json`)
```json
{
  "timestamp": "2025-01-15T10:30:00",
  "freshness_score": 0.85,
  "networks_checked": 13,
  "networks_with_fresh_data": 11,
  "networks_with_stale_data": 2,
  "stale_networks": ["network1", "network2"],
  "validation_errors": [],
  "validation_warnings": ["Invalid timestamp for USDC in polygon"],
  "oldest_data_age_hours": 4.5,
  "newest_data_age_hours": 0.25
}
```

## Usage Examples

### Basic Monitoring
```bash
# Run with debug logging
python aave_fetcher.py --debug

# Run with file logging
python aave_fetcher.py --log-file aave_fetcher.log
```

### Comprehensive Monitoring
```bash
# Full monitoring with all reports
python aave_fetcher.py \
  --debug \
  --log-file aave_fetcher.log \
  --save-debug-report \
  --save-performance-report \
  --validate-freshness \
  --include-rpc-history
```

### Production Monitoring
```bash
# Optimized for GitHub Actions
python aave_fetcher.py \
  --ultra-fast \
  --save-performance-report \
  --validate-freshness \
  --timeout 60
```

### Troubleshooting Mode
```bash
# Maximum debugging information
python aave_fetcher.py \
  --sequential \
  --debug \
  --log-file debug.log \
  --save-debug-report \
  --include-rpc-history \
  --timeout 120
```

## Monitoring in GitHub Actions

The monitoring features are designed to work seamlessly in GitHub Actions:

1. **Performance Compliance**: Tracks execution time against GitHub Actions limits
2. **Error Reporting**: Provides detailed error context for workflow failures
3. **Health Notifications**: Creates formatted notifications for workflow status
4. **Report Artifacts**: Saves monitoring reports as workflow artifacts

### Example GitHub Actions Integration
```yaml
- name: Run Aave Data Fetcher with Monitoring
  run: |
    python aave_fetcher.py \
      --ultra-fast \
      --save-performance-report \
      --validate-freshness \
      --log-file fetcher.log

- name: Upload Monitoring Reports
  if: always()
  uses: actions/upload-artifact@v3
  with:
    name: monitoring-reports
    path: |
      performance_report.json
      health_report.json
      freshness_report.json
      fetcher.log
```

## Interpreting Results

### Performance Metrics
- **Success Rate**: Should be >90% for healthy operation
- **Average RPC Time**: Should be <2s for good performance
- **Network Time**: Should be <60s per network for GitHub Actions compliance

### Health Indicators
- **Healthy**: All endpoints responding normally
- **Degraded**: Primary endpoint down but fallbacks available
- **Unhealthy**: No healthy endpoints available

### Freshness Scores
- **>90%**: Excellent data freshness
- **70-90%**: Good data freshness
- **<70%**: Poor data freshness, investigate stale networks

## Troubleshooting

### Common Issues

1. **Low RPC Success Rate**
   - Check network connectivity
   - Verify RPC endpoint status
   - Consider increasing timeout values

2. **Slow Performance**
   - Review performance report for bottlenecks
   - Check RPC response times
   - Consider using --turbo mode

3. **Stale Data**
   - Check freshness report for affected networks
   - Verify timestamp fields in responses
   - Investigate network-specific issues

### Debug Workflow
1. Enable debug logging: `--debug --log-file debug.log`
2. Save comprehensive reports: `--save-debug-report --include-rpc-history`
3. Validate data freshness: `--validate-freshness`
4. Review generated reports for specific issues
5. Use sequential mode for detailed troubleshooting: `--sequential`

## Integration with Existing Features

The monitoring system integrates seamlessly with:
- **Graceful Fetcher**: Enhanced error reporting and retry monitoring
- **Ultra-Fast Fetcher**: Performance profiling for Multicall3 operations
- **Validation System**: Extended with freshness validation
- **Health Monitoring**: Enhanced endpoint health checks
- **GitHub Actions**: Automated reporting and compliance checking

This comprehensive monitoring system ensures reliable operation, easy troubleshooting, and optimal performance of the Aave V3 data fetcher.