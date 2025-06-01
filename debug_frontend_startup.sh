#!/bin/bash

# Debug script for frontend startup issues

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Frontend Startup Debug Script${NC}"
echo "=============================="

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Navigate to frontend
cd admin_panel/frontend

echo -e "\n${YELLOW}Frontend Directory:${NC}"
pwd
echo ""

echo -e "${YELLOW}Directory Structure:${NC}"
echo "src/ contents:"
find src -type f -name "*.ts" -o -name "*.tsx" | head -20
echo ""

echo -e "${YELLOW}Checking critical files:${NC}"
if [ -f "src/lib/utils.ts" ]; then
    echo "✓ src/lib/utils.ts exists"
    echo "  Contents:"
    head -5 src/lib/utils.ts
else
    echo "✗ src/lib/utils.ts MISSING!"
fi
echo ""

echo -e "${YELLOW}Vite Config:${NC}"
if [ -f "vite.config.ts" ]; then
    echo "✓ vite.config.ts exists"
    cat vite.config.ts
else
    echo "✗ vite.config.ts MISSING!"
fi
echo ""

echo -e "${YELLOW}TypeScript Config:${NC}"
if [ -f "tsconfig.json" ]; then
    echo "✓ tsconfig.json exists"
    grep -A5 '"paths"' tsconfig.json || echo "No paths configuration found"
else
    echo "✗ tsconfig.json MISSING!"
fi
echo ""

echo -e "${YELLOW}Package.json scripts:${NC}"
grep -A5 '"scripts"' package.json
echo ""

echo -e "${YELLOW}Node/npm versions:${NC}"
echo "Node: $(node --version)"
echo "npm: $(npm --version)"
echo ""

echo -e "${YELLOW}Current working directory:${NC}"
pwd
echo ""

echo -e "${YELLOW}Environment variables:${NC}"
echo "NODE_PATH=$NODE_PATH"
echo "PWD=$PWD"
echo ""

# Try to start vite with more debugging
echo -e "${YELLOW}Starting Vite with debug output:${NC}"
echo "Command: npm run dev"
echo ""

# Clear any problematic environment variables
unset NODE_PATH

# Run vite directly for debugging
npx vite --debug