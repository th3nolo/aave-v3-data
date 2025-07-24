# Traffic Analytics Setup Guide

This guide explains how to set up GitHub traffic analytics using a secure fine-grained personal access token.

## Why Fine-Grained Tokens?

Fine-grained personal access tokens are GitHub's recommended approach for API access:
- **Minimal permissions**: Only grants access to what's needed
- **Repository-specific**: Limited to a single repository
- **Time-limited**: Expires after a set period
- **More secure**: Follows the principle of least privilege

## Setup Instructions

### 1. Create Fine-Grained Token

1. Navigate to: https://github.com/settings/personal-access-tokens/new
2. Fill in the token details:
   - **Token name**: `AAVE Traffic Analytics Read-Only`
   - **Expiration**: 90 days
   - **Description**: "Read traffic data and commit updates for aave-v3-data"

3. Under **Repository access**:
   - Select: **Selected repositories**
   - Add: `th3nolo/aave-v3-data`

4. Under **Permissions**, set ONLY:
   - **Repository permissions → Contents**: `Read and write`
   - **Repository permissions → Administration**: `Read`
   - Leave all other permissions as "No access"

5. Click **Generate token**
6. **IMPORTANT**: Copy the token immediately (you won't see it again!)

### 2. Add Token to Repository

1. Go to your repository: https://github.com/th3nolo/aave-v3-data
2. Navigate to: Settings → Secrets and variables → Actions
3. Click **New repository secret**
4. Add:
   - **Name**: `TRAFFIC_TOKEN`
   - **Secret**: Paste your fine-grained token
5. Click **Add secret**

### 3. Test the Workflow

You can manually trigger the workflow to test:
```bash
gh workflow run traffic-analytics.yml --ref main
```

## Security Notes

- **Token expiration**: Set a calendar reminder to renew your token before it expires
- **Minimal permissions**: The token only has read access to traffic data and write access to commit files
- **Repository-scoped**: The token only works with the specified repository
- **Encrypted storage**: GitHub stores secrets encrypted and never exposes them in logs

## What Data is Collected?

The workflow collects:
- **Views**: Page views and unique visitors
- **Clones**: Git clones and unique cloners
- **Referrers**: Top traffic sources
- **Popular paths**: Most visited pages

Data is stored in `/traffic_data/` directory and updated daily.

## Troubleshooting

If the workflow fails:
1. Check token expiration date
2. Verify the `TRAFFIC_TOKEN` secret exists
3. Ensure permissions are set correctly (Contents: write, Administration: read)
4. Check workflow logs for specific error messages

## Token Renewal

When your token expires:
1. Create a new fine-grained token with the same permissions
2. Update the `TRAFFIC_TOKEN` secret with the new value
3. Delete the old token from your GitHub settings