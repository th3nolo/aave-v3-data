#!/bin/bash
# Run graceful fetcher with health checks enabled

echo "Running graceful fetcher with health checks enabled..."
ENABLE_RPC_MONITORING=true python src/graceful_fetcher.py