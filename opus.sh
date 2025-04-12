#!/bin/bash

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════╗"
echo "║                    OPUS                      ║"
echo "╚══════════════════════════════════════════════╝"
echo -e "${NC}"

run_command() {
    local cmd="$1"
    local description="$2"
    
    echo -ne "${YELLOW}${description}...${NC}"
    
    if $cmd > /dev/null 2>&1; then
        echo -e "\r${GREEN}✓ ${description} completed successfully${NC}"
        return 0
    else
        echo -e "\r${RED}✗ ${description} failed${NC}"
        return 1
    fi
}

if ! run_command "bash clean.sh" "Running cleanup"; then
    echo -e "${RED}Error: Cleanup failed. Check clean.sh for errors.${NC}"
    exit 1
fi

echo -e "\n${BLUE}Starting application...${NC}"
if ! run_command "bash start" "Starting application"; then
    echo -e "${RED}Error: Application failed to start. Check start script.${NC}"
    exit 1
fi

echo -e "\n${BLUE}╔══════════════════════════════════════════════╗"
echo -e "║    ${GREEN}OPUS sequence completed${BLUE}    ║"
echo -e "╚══════════════════════════════════════════════╝${NC}"
