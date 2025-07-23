# Comprehensive Deployment Guide

This guide provides step-by-step instructions for deploying the Aave V3 Data Fetcher with GitHub Pages, including troubleshooting for common issues and 2025 network expansions.

## 📋 Prerequisites

- GitHub account (free tier sufficient)
- Basic understanding of Git and GitHub
- No programming experience required for basic setup

## 🚀 Quick Start Deployment

### Step 1: Repository Creation

#### Option A: Fork This Repository (Recommended)
1. Go to the source repository on GitHub
2. Click **Fork** button in top-right corner
3. Choose your GitHub account as destination
4. Keep repository name or customize it
5. Ensure repository is **Public** (required for free GitHub Pages)

#### Option B: Create New Repository
1. Create new public repository on GitHub
2. Clone this repository locally:
   ```bash
   git clone https://github.com/original-repo/aave-v3-data-fetcher.git
   cd aave-v3-data-fetcher
   ```
3. Change remote origin to your repository:
   ```bash
   git remote set-url origin https://github.com/YOUR-USERNAME/YOUR-REPO-NAME.git
   git push -u origin main
   ```

### Step 2: Configure GitHub Pages

1. **Navigate to Repository Settings**
   - Go to your repository on GitHub
   - Click **Settings** tab (requires repository admin access)

2. **Enable GitHub Pages**
   - Scroll to **Pages** section in left sidebar
   - **Source**: Select "Deploy from a branch"
   - **Branch**: Select `main`
   - **Folder**: Select `/ (root)`
   - Click **Save**

3. **Verify Pages Configuration**
   - You should see: "Your site is ready to be published at `https://YOUR-USERNAME.github.io/YOUR-REPO-NAME/`"
   - Initial deployment takes 5-10 minutes

### Step 3: Configure GitHub Actions

1. **Set Actions Permissions**
   - Go to **Settings** → **Actions** → **General**
   - **Actions permissions**: "Allow all actions and reusable workflows"
   - **Workflow permissions**: "Read and write permissions"
   - ✅ Check "Allow GitHub Actions to create and approve pull requests"
   - Click **Save**

2. **Verify Workflow File**
   - Ensure `.github/workflows/update-aave-data.yml` exists in your repository
   - File should contain the automated update workflow

### Step 4: Initial Test Run

1. **Manual Workflow Trigger**
   - Go to **Actions** tab in your repository
   - Click **Update Aave V3 Data** workflow
   - Click **Run workflow** → **Run workflow**

2. **Monitor Execution**
   - Watch workflow progress (typically 2-5 minutes)
   - Check for green checkmark indicating success
   - Review logs if any errors occur

3. **Verify Generated Files**
   - Check repository for new files:
     - `aave_v3_data.json` - JSON data
     - `aave_v3_data.html` - HTML page
     - `health_report.json` - System health
     - `validation_report.json` - Data validation

### Step 5: Access Your Data

After successful deployment:

#### HTML Interface
```
https://YOUR-USERNAME.github.io/YOUR-REPO-NAME/aave_v3_data.html
```

#### JSON API
```
https://raw.githubusercontent.com/YOUR-USERNAME/YOUR-REPO-NAME/main/aave_v3_data.json
```

## 🔧 Advanced Configuration

### Custom Domain Setup (Optional)

1. **Purchase Domain** (if you don't have one)
2. **Configure DNS**
   - Add CNAME record: `www.yourdomain.com` → `YOUR-USERNAME.github.io`
   - Add A records for apex domain (if desired)
3. **GitHub Pages Configuration**
   - Go to repository **Settings** → **Pages**
   - Add custom domain in **Custom domain** field
   - Enable **Enforce HTTPS**

### Workflow Customization

Edit `.github/workflows/update-aave-data.yml` to customize:

```yaml
# Change update frequency
schedule:
  - cron: '0 */6 * * *'  # Every 6 hours instead of daily

# Add notifications
- name: Notify on failure
  if: failure()
  uses: actions/github-script@v6
  with:
    script: |
      github.rest.issues.create({
        owner: context.repo.owner,
        repo: context.repo.repo,
        title: 'Aave Data Fetch Failed',
        body: 'The automated data fetch workflow failed. Check the logs.'
      })
```

### Performance Optimization

For faster execution, modify the workflow to use turbo mode:

```yaml
- name: Run Aave Data Fetcher
  run: python aave_fetcher.py --turbo --validate
```

## 🌐 Network Extensions (2025 Updates)

### Automatic Network Discovery

The system automatically discovers new Aave V3 networks through integration with the aave-address-book:

1. **Auto-Update Feature**
   - Fetches latest network configurations from bgd-labs/aave-address-book
   - Automatically includes new Aave V3 deployments
   - Validates new network configurations

2. **Manual Network Addition**
   
   To manually add a new network, edit `src/networks.py`:

   ```python
   # Add new network to AAVE_V3_NETWORKS dictionary
   'new_network': {
       'rpc': 'https://rpc.new-network.com',
       'pool': '0x...',  # Aave V3 Pool contract address
       'name': 'New Network Name',
       'chain_id': 12345,
       'fallback_rpcs': [
           'https://backup-rpc.new-network.com',
           'https://another-backup.new-network.com'
       ]
   }
   ```

3. **Network Validation**
   
   Test new networks locally:
   ```bash
   # Validate network configuration
   python -c "from src.networks import validate_all_networks; print(validate_all_networks())"
   
   # Test specific network
   python aave_fetcher.py --networks new_network --validate
   ```

### Expected 2025 Networks

The system is prepared for these additional networks:
- **Mantle** - Layer 2 scaling solution
- **Soneium** - Sony blockchain network  
- **Sonic** - High-performance blockchain
- **Linea** - ConsenSys zkEVM
- **zkSync Era** - Matter Labs zkEVM
- **Additional L2s** - As Aave V3 expands

## 🔍 Troubleshooting Guide

### Common Deployment Issues

#### Issue: "Pages build and deployment" Failed

**Symptoms:**
- GitHub Pages shows deployment failure
- HTML page not accessible
- Error in Pages deployment logs

**Solutions:**
1. **Check Repository Visibility**
   ```bash
   # Ensure repository is public
   # Go to Settings → General → Danger Zone
   # Change visibility to Public if needed
   ```

2. **Verify HTML File**
   ```bash
   # Check if HTML file exists and is valid
   python -c "import os; print('HTML exists:', os.path.exists('aave_v3_data.html'))"
   ```

3. **Check File Size**
   ```bash
   # GitHub Pages has file size limits
   ls -lh aave_v3_data.html
   # If >100MB, optimize HTML generation
   ```

#### Issue: Workflow Permissions Error

**Symptoms:**
- Workflow fails with "Permission denied" error
- Cannot commit generated files
- Error: "Resource not accessible by integration"

**Solutions:**
1. **Fix Workflow Permissions**
   - Settings → Actions → General
   - Workflow permissions: "Read and write permissions"
   - ✅ "Allow GitHub Actions to create and approve pull requests"

2. **Check Repository Settings**
   - Ensure Actions are enabled
   - Verify workflow file permissions

#### Issue: RPC Endpoint Failures (2025 Network Expansion)

**Symptoms:**
- High failure rates in health_report.json
- Missing data for specific networks
- Timeout errors in workflow logs

**Solutions:**
1. **Check RPC Health**
   ```bash
   # Test RPC endpoints
   python -c "from src.networks import test_all_rpc_endpoints; print(test_all_rpc_endpoints())"
   ```

2. **Update RPC Endpoints**
   ```python
   # In src/networks.py, add more fallback RPCs
   'ethereum': {
       'rpc': 'https://rpc.ankr.com/eth',
       'fallback_rpcs': [
           'https://eth.llamarpc.com',
           'https://ethereum.publicnode.com',
           'https://eth.rpc.blxrbdn.com'
       ]
   }
   ```

3. **Rate Limiting Solutions**
   ```bash
   # Use sequential mode to reduce concurrent requests
   python aave_fetcher.py --sequential --timeout 120
   ```

#### Issue: Data Validation Failures

**Symptoms:**
- validation_report.json shows errors
- Known parameter values don't match
- Inconsistent data across runs

**Solutions:**
1. **Check Protocol Updates**
   ```bash
   # Run 2025 parameter validation
   python validate_2025_parameters.py --verbose
   ```

2. **Update Known Values**
   ```python
   # In src/validation.py, update expected values
   KNOWN_VALUES_2025 = {
       'ethereum': {
           'USDC': {'liquidation_threshold': 0.78}  # Updated value
       }
   }
   ```

3. **Tolerance Adjustment**
   ```python
   # Adjust validation tolerance for volatile parameters
   VALIDATION_TOLERANCES = {
       'supply_cap': 0.25,  # 25% tolerance for caps
       'borrow_cap': 0.25
   }
   ```

### Performance Issues

#### Issue: GitHub Actions Timeout

**Symptoms:**
- Workflow exceeds 10-minute limit
- Incomplete data fetching
- Performance degradation

**Solutions:**
1. **Use Turbo Mode**
   ```yaml
   # In .github/workflows/update-aave-data.yml
   - name: Run Aave Data Fetcher
     run: python aave_fetcher.py --turbo --timeout 60
   ```

2. **Network Prioritization**
   ```python
   # In src/networks.py, prioritize critical networks
   PRIORITY_NETWORKS = ['ethereum', 'polygon', 'arbitrum', 'optimism']
   ```

3. **Optimize Multicall3**
   ```bash
   # Use ultra-fast mode with Multicall3 optimization
   python aave_fetcher.py --ultra-fast --validate
   ```

#### Issue: Memory Usage

**Symptoms:**
- Out of memory errors in GitHub Actions
- Slow performance with large datasets
- Workflow killed unexpectedly

**Solutions:**
1. **Optimize Data Structures**
   ```python
   # Process networks sequentially for large datasets
   python aave_fetcher.py --sequential --save-memory
   ```

2. **Reduce Concurrent Workers**
   ```python
   # In src/ultra_fast_fetcher.py
   MAX_WORKERS = min(4, len(networks))  # Reduce from 8
   ```

### Data Quality Issues

#### Issue: Stale Data

**Symptoms:**
- Old timestamps in JSON metadata
- Data not updating daily
- Freshness validation failures

**Solutions:**
1. **Check Workflow Schedule**
   ```yaml
   # Verify cron schedule in workflow
   schedule:
     - cron: '0 0 * * *'  # Daily at midnight UTC
   ```

2. **Manual Trigger**
   ```bash
   # Trigger workflow manually
   # Go to Actions → Update Aave V3 Data → Run workflow
   ```

3. **Validate Timestamps**
   ```bash
   python aave_fetcher.py --validate-freshness
   ```

#### Issue: Missing Networks

**Symptoms:**
- Expected networks not in output
- Lower network count than expected
- Missing data for new 2025 networks

**Solutions:**
1. **Check Network Configuration**
   ```bash
   python -c "from src.networks import get_active_networks; print(list(get_active_networks().keys()))"
   ```

2. **Validate New Networks**
   ```bash
   # Test specific network
   python aave_fetcher.py --networks mantle,soneium --debug
   ```

3. **Update Address Book**
   ```bash
   # Force refresh of network configurations
   python -c "from src.networks import refresh_address_book; refresh_address_book()"
   ```

## 📊 Monitoring and Maintenance

### Health Monitoring

1. **Daily Health Checks**
   ```bash
   # Check health report
   curl -s https://raw.githubusercontent.com/YOUR-USERNAME/YOUR-REPO/main/health_report.json | jq .
   ```

2. **Performance Monitoring**
   ```bash
   # Monitor execution times
   curl -s https://raw.githubusercontent.com/YOUR-USERNAME/YOUR-REPO/main/performance_report.json | jq .overall_stats
   ```

3. **Validation Monitoring**
   ```bash
   # Check validation status
   curl -s https://raw.githubusercontent.com/YOUR-USERNAME/YOUR-REPO/main/validation_report.json | jq .summary
   ```

### Automated Alerts

Set up GitHub Issues for failures:

```yaml
# Add to workflow
- name: Create issue on failure
  if: failure()
  uses: actions/github-script@v6
  with:
    script: |
      const title = 'Aave Data Fetch Failed - ' + new Date().toISOString().split('T')[0];
      const body = `
      The automated Aave V3 data fetch failed.
      
      **Workflow Run:** ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}
      **Timestamp:** ${new Date().toISOString()}
      
      Please check the workflow logs for details.
      `;
      
      github.rest.issues.create({
        owner: context.repo.owner,
        repo: context.repo.repo,
        title: title,
        body: body,
        labels: ['bug', 'automated']
      });
```

### Maintenance Tasks

#### Weekly Tasks
- Review health_report.json for RPC endpoint issues
- Check validation_report.json for parameter changes
- Monitor GitHub Actions usage limits

#### Monthly Tasks
- Update RPC endpoint configurations
- Review and update known parameter values
- Check for new Aave V3 network deployments
- Update documentation for any changes

#### Quarterly Tasks
- Review and optimize performance settings
- Update validation tolerances based on protocol changes
- Audit and update fallback RPC endpoints
- Review GitHub Actions workflow efficiency

## 🔐 Security Considerations

### Repository Security
- Keep repository public (required for free GitHub Pages)
- No sensitive data stored in repository
- All RPC endpoints are public
- No API keys or secrets required

### Workflow Security
- Minimal permissions (read blockchain data only)
- No external dependencies beyond Python standard library
- Automated security updates via Dependabot
- Regular security audits of RPC endpoints

### Data Security
- All data is publicly available on-chain
- No personal or sensitive information processed
- Read-only operations only
- No transaction capabilities

## 📈 Scaling and Optimization

### For High-Traffic Usage

1. **CDN Integration**
   ```html
   <!-- Use CDN for faster global access -->
   <link rel="dns-prefetch" href="//raw.githubusercontent.com">
   ```

2. **Caching Strategy**
   ```javascript
   // Implement client-side caching
   const CACHE_DURATION = 30 * 60 * 1000; // 30 minutes
   ```

3. **Load Balancing**
   ```python
   # Distribute requests across multiple RPC endpoints
   RPC_POOLS = {
       'ethereum': [
           'https://rpc.ankr.com/eth',
           'https://eth.llamarpc.com',
           'https://ethereum.publicnode.com'
       ]
   }
   ```

### For Enterprise Usage

1. **Private Repository Setup**
   - Use GitHub Pro/Team for private repositories
   - Configure GitHub Pages for private repos
   - Set up custom authentication if needed

2. **Enhanced Monitoring**
   - Integrate with external monitoring services
   - Set up custom alerting systems
   - Implement detailed analytics

3. **Custom Deployment**
   - Deploy to custom infrastructure
   - Use container orchestration
   - Implement blue-green deployments

## 🆘 Support and Resources

### Getting Help

1. **GitHub Issues**
   - Report bugs and request features
   - Search existing issues first
   - Provide detailed error information

2. **Documentation**
   - README.md - Overview and quick start
   - USAGE.md - Detailed usage instructions
   - TESTING_GUIDE.md - Testing and validation
   - MONITORING_GUIDE.md - Monitoring and debugging

3. **Community Resources**
   - Aave Discord for protocol questions
   - GitHub Discussions for general questions
   - Stack Overflow for technical issues

### Useful Links

- [Aave V3 Documentation](https://docs.aave.com/developers/)
- [GitHub Pages Documentation](https://docs.github.com/en/pages)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Aave Address Book](https://github.com/bgd-labs/aave-address-book)

---

**Deployment Complete!** Your Aave V3 Data Fetcher should now be running automatically and serving fresh data daily.

For questions or issues, please refer to the troubleshooting section above or open an issue in the repository.