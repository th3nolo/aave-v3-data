# GitHub Pages Setup Guide

This guide provides step-by-step instructions for configuring your repository for GitHub Pages deployment with the Aave V3 Data Fetcher.

## 📋 Prerequisites

- GitHub account
- Public repository (GitHub Pages requires public repos for free accounts)
- Repository with Aave V3 Data Fetcher code

## 🔧 Repository Configuration

### Step 1: Repository Settings

1. **Navigate to Repository Settings**
   - Go to your repository on GitHub
   - Click the **Settings** tab (requires admin access)

2. **Verify Repository Visibility**
   - Scroll to **Danger Zone** at bottom of Settings
   - Ensure repository is **Public** (required for free GitHub Pages)
   - If private, click **Change visibility** → **Make public**

### Step 2: Enable GitHub Pages

1. **Access Pages Settings**
   - In repository Settings, scroll to **Pages** in left sidebar
   - Click **Pages**

2. **Configure Source**
   - **Source**: Select "Deploy from a branch"
   - **Branch**: Select `main` (or your default branch)
   - **Folder**: Select `/ (root)`
   - Click **Save**

3. **Verify Configuration**
   - You should see: "Your site is ready to be published at `https://[username].github.io/[repo-name]/`"
   - Initial deployment may take a few minutes

### Step 3: Configure GitHub Actions Permissions

1. **Access Actions Settings**
   - In repository Settings, click **Actions** → **General**

2. **Set Actions Permissions**
   - **Actions permissions**: Select "Allow all actions and reusable workflows"
   - Click **Save**

3. **Configure Workflow Permissions**
   - **Workflow permissions**: Select "Read and write permissions"
   - Check ✅ "Allow GitHub Actions to create and approve pull requests"
   - Click **Save**

### Step 4: Test Initial Deployment

1. **Manual Workflow Trigger**
   - Go to **Actions** tab in your repository
   - Click **Update Aave V3 Data** workflow
   - Click **Run workflow** → **Run workflow**

2. **Monitor Execution**
   - Watch the workflow execution in real-time
   - Check for any errors in the logs
   - Verify successful completion (green checkmark)

3. **Verify File Generation**
   - After successful run, check repository for:
     - `aave_v3_data.json` - JSON data file
     - `aave_v3_data.html` - HTML page
     - `health_report.json` - Health monitoring
     - `validation_report.json` - Data validation

## 🌐 Access Your Data

### HTML Interface
```
https://[username].github.io/[repository-name]/aave_v3_data.html
```

### JSON API
```
https://raw.githubusercontent.com/[username]/[repository-name]/main/aave_v3_data.json
```

### Example URLs
If your GitHub username is `johndoe` and repository is `aave-data`:
- **HTML**: https://johndoe.github.io/aave-data/aave_v3_data.html
- **JSON**: https://raw.githubusercontent.com/johndoe/aave-data/main/aave_v3_data.json

## 🔄 Automated Updates

### Daily Schedule
The system automatically runs daily at midnight UTC:
```yaml
schedule:
  - cron: '0 0 * * *'  # Daily at midnight UTC
```

### Manual Triggers
You can manually trigger updates:
1. Go to **Actions** tab
2. Select **Update Aave V3 Data**
3. Click **Run workflow**
4. Click **Run workflow** button

## 🔍 Monitoring and Troubleshooting

### Check Workflow Status
1. **Actions Tab**: View execution history
2. **Workflow Logs**: Click on individual runs for detailed logs
3. **Status Badges**: Add to README for quick status visibility

### Common Issues and Solutions

#### Issue: "Pages build and deployment" failing
**Solution**: 
- Ensure repository is public
- Check that HTML file is valid
- Verify Pages is enabled in Settings

#### Issue: Workflow permissions error
**Solution**:
- Go to Settings → Actions → General
- Set workflow permissions to "Read and write permissions"
- Enable "Allow GitHub Actions to create and approve pull requests"

#### Issue: No data files generated
**Solution**:
- Check workflow logs for Python script errors
- Verify RPC endpoints are accessible
- Check network configurations in `src/networks.py`

#### Issue: JSON/HTML files not updating
**Solution**:
- Verify workflow completed successfully
- Check if data actually changed (no commit if no changes)
- Ensure GitHub Pages is rebuilding (check Pages settings)

### Health Monitoring

The system generates several monitoring files:

1. **health_report.json**: RPC endpoint health status
2. **validation_report.json**: Data validation results
3. **Workflow logs**: Execution performance metrics

## 🎯 Advanced Configuration

### Custom Domain (Optional)
1. In Pages settings, add your custom domain
2. Configure DNS CNAME record pointing to `[username].github.io`
3. Enable HTTPS enforcement

### Branch Protection (Recommended)
1. Go to Settings → Branches
2. Add rule for `main` branch
3. Enable "Restrict pushes that create files"
4. Allow GitHub Actions to bypass restrictions

### Notifications
1. Go to Settings → Notifications
2. Configure email notifications for workflow failures
3. Set up Slack/Discord webhooks if needed

## 📊 Performance Optimization

### Execution Time Monitoring
- GitHub Actions has 10-minute limit for free accounts
- System typically completes in 2-5 minutes
- Monitor execution times in workflow logs

### Network Prioritization
Critical networks are processed first:
1. Ethereum (highest TVL)
2. Polygon (high volume)
3. Arbitrum (major L2)
4. Other networks

### Failure Handling
- Individual network failures don't stop execution
- Graceful degradation continues with available networks
- Detailed error reporting in logs

## 🔐 Security Best Practices

### Repository Security
- Keep repository public (required for free Pages)
- No sensitive data in repository
- Use only public RPC endpoints
- No API keys or secrets required

### Workflow Security
- Minimal permissions (read blockchain data only)
- No external dependencies
- Standard library Python only
- Automated security updates via Dependabot

## 📈 Usage Analytics

### GitHub Insights
- Go to repository **Insights** tab
- View **Traffic** for page views
- Monitor **Actions** usage

### Data Access Patterns
- HTML interface: Human users
- JSON API: Programmatic access, LLMs
- Raw files: Direct data consumption

## 🆘 Support and Resources

### Documentation
- [GitHub Pages Docs](https://docs.github.com/en/pages)
- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [Aave V3 Docs](https://docs.aave.com/developers/)

### Community
- GitHub Issues for bug reports
- GitHub Discussions for questions
- Aave Discord for protocol questions

### Troubleshooting Checklist
- [ ] Repository is public
- [ ] GitHub Pages enabled from main branch root
- [ ] Actions have read/write permissions
- [ ] Workflow completed successfully
- [ ] Data files exist in repository
- [ ] Pages deployment completed
- [ ] URLs are accessible

---

**Need Help?** Open an issue in the repository with:
- Error messages from workflow logs
- Repository settings screenshots
- Expected vs actual behavior