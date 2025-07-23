# Aave V3 Data Fetcher - Testing and Validation Guide

This document describes the comprehensive testing and validation system implemented for the Aave V3 Data Fetcher project.

## Overview

The testing system includes multiple layers of validation:

1. **Local Test Runner** - Comprehensive functionality testing
2. **Protocol Parameter Validation** - Validates against known protocol values
3. **2025 Risk Parameter Validation** - Validates new 2025 risk updates
4. **Workflow Integration Tests** - End-to-end workflow testing
5. **Quick Validation** - Fast basic checks

## Test Scripts

### 1. Main Test Runner (`test_runner.py`)

Comprehensive test suite that validates script functionality and data accuracy.

```bash
# Run all tests with data fetching
python test_runner.py --full

# Run quick tests without data fetching
python test_runner.py --quick

# Run validation tests only (requires existing data)
python test_runner.py --validation-only

# Save test reports
python test_runner.py --full --save-reports
```

**Features:**
- Network configuration validation
- Data fetching tests (graceful and ultra-fast modes)
- Comprehensive data validation
- JSON schema validation
- Performance compliance testing
- Known protocol value checks

### 2. Protocol Parameter Validator (`validate_protocol_parameters.py`)

Validates fetched data against known protocol values with 2025 updates.

```bash
# Validate against known values
python validate_protocol_parameters.py

# Save detailed comparison report
python validate_protocol_parameters.py --save-report

# Verbose output
python validate_protocol_parameters.py --verbose
```

**Features:**
- Validates critical parameters (LT, LTV, decimals) with strict tolerance
- Validates standard parameters (liquidation bonus, reserve factor)
- Validates boolean parameters (active, borrowing enabled, etc.)
- Validates supply/borrow caps (2025 feature)
- Generates detailed comparison reports

### 3. 2025 Risk Parameter Validator (`validate_2025_parameters.py`)

Specifically validates 2025 risk parameter updates and new features.

```bash
# Validate 2025 updates
python validate_2025_parameters.py

# Save detailed validation report
python validate_2025_parameters.py --save-report

# Verbose output with details
python validate_2025_parameters.py --verbose
```

**Features:**
- Supply/borrow caps validation
- WBTC risk parameter adjustments
- Stablecoin reserve factor increases
- DAI LTV adjustment on Ethereum
- Polygon USDC collateral disable validation
- Network expansion validation

### 4. Workflow Integration Tester (`test_workflow_integration.py`)

Tests complete workflows and integration scenarios.

```bash
# Run integration tests
python test_workflow_integration.py

# Quick integration tests
python test_workflow_integration.py --quick

# Full integration test suite
python test_workflow_integration.py --full

# Save test outputs
python test_workflow_integration.py --save-outputs
```

**Features:**
- Complete graceful workflow testing
- Complete ultra-fast workflow testing
- Network expansion scenarios
- Error recovery testing
- Performance compliance testing
- Data consistency across runs
- Output format compatibility

### 5. Complete Test Suite Runner (`run_all_tests.py`)

Runs all test scripts in sequence with proper coordination.

```bash
# Run complete test suite
python run_all_tests.py

# Quick tests only
python run_all_tests.py --quick

# Validation tests only
python run_all_tests.py --validation-only

# Integration tests only
python run_all_tests.py --integration-only

# Fetch fresh data and run all tests
python run_all_tests.py --fetch-data --save-reports
```

### 6. Quick Validation (`validate_fixes.py`)

Fast validation for basic functionality checks.

```bash
# Quick validation
python validate_fixes.py

# Network configuration only
python validate_fixes.py --network-only
```

## Known Protocol Values (2025 Updates)

The validation system includes updated protocol values for 2025:

### WBTC Risk Parameter Updates
- **Liquidation Threshold**: 0.70 → 0.78
- **Loan-to-Value**: 0.65 → 0.73
- **Liquidation Bonus**: 0.10 → 0.05
- **Reserve Factor**: 0.20 → 0.50

### Stablecoin Reserve Factor Increases
- **Polygon USDC**: 0.10 → 0.60
- **Polygon USDC.e**: 0.10 → 0.60
- **Arbitrum USDC.e**: 0.10 → 0.50
- **Optimism USDC/USDC.e**: 0.10 → 0.50

### DAI LTV Adjustment
- **Ethereum DAI LTV**: 0.75 → 0.63

### Polygon Native USDC
- **Polygon USDC LTV**: Disabled (0.00) - cannot be used as collateral

### Supply/Borrow Caps
New feature introduced in 2025 for risk management across all networks.

## Network Expansion (2025)

Expected networks for 2025:
- Ethereum, Polygon, Arbitrum, Optimism, Avalanche
- Metis, Base, Gnosis, BNB, Scroll
- Celo, Mantle, Soneium, Sonic

Minimum expected: 12+ networks

## Test Reports

When `--save-reports` is used, the following reports are generated:

1. **test_report.json** - Main test execution results
2. **validation_report.json** - Data validation details
3. **protocol_parameter_comparison.json** - Parameter comparison report
4. **risk_2025_validation_report.json** - 2025 updates validation
5. **integration_test_report.json** - Integration test results

## Usage Examples

### Daily Validation Workflow
```bash
# 1. Fetch fresh data
python aave_fetcher.py --ultra-fast --validate

# 2. Run quick validation
python validate_fixes.py

# 3. Run comprehensive validation if needed
python validate_protocol_parameters.py --verbose
```

### Development Testing
```bash
# 1. Test network configuration
python validate_fixes.py --network-only

# 2. Run integration tests
python test_workflow_integration.py --quick

# 3. Validate 2025 features
python validate_2025_parameters.py
```

### CI/CD Pipeline
```bash
# Complete automated testing
python run_all_tests.py --fetch-data --save-reports
```

## Performance Expectations

- **Quick validation**: < 5 seconds
- **Network configuration**: < 1 second
- **Data validation**: < 30 seconds
- **Integration tests**: < 5 minutes
- **Complete test suite**: < 10 minutes

## Error Handling

The testing system includes comprehensive error handling:

- **Network failures**: Graceful degradation with partial data
- **RPC timeouts**: Retry logic and fallback endpoints
- **Data inconsistencies**: Detailed error reporting
- **Schema violations**: Clear validation messages

## Tolerance Settings

- **Critical parameters** (LT, LTV): 5% tolerance
- **Standard parameters**: 15% tolerance
- **Supply/borrow caps**: 25% tolerance (more volatile)
- **Boolean parameters**: Exact match required

## Integration with Main Fetcher

The validation system integrates with the main fetcher:

```python
# In aave_fetcher.py
if args.validate:
    validation_passed, validation_summary = run_comprehensive_validation(data)
```

This ensures data quality before output generation.

## Troubleshooting

### Common Issues

1. **Missing data file**: Run `python aave_fetcher.py` first
2. **Network configuration errors**: Check RPC endpoints in `src/networks.py`
3. **Validation failures**: Review parameter updates in validation scripts
4. **Performance issues**: Use `--quick` mode for faster testing

### Debug Mode

For detailed debugging, use verbose flags:
```bash
python test_runner.py --full --verbose
python validate_protocol_parameters.py --verbose
```

## Continuous Integration

The testing system is designed for CI/CD integration:

- Exit codes indicate success/failure
- JSON reports for automated processing
- Performance monitoring for GitHub Actions compliance
- Comprehensive logging for debugging

This testing system ensures the Aave V3 Data Fetcher maintains high quality and accuracy as the protocol evolves and expands to new networks.