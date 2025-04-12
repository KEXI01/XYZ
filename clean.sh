#!/bin/bash

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════╗"
echo "║           VX System Cleaner                  ║"
echo "╚══════════════════════════════════════════════╝"
echo -e "${NC}"

echo -e "${YELLOW}Changing to VX7 directory...${NC}"
if ! cd ~/XYZ 2>/dev/null; then
    echo -e "${RED}Error: Failed to change to ~/VX7 directory. Does it exist?${NC}"
    exit 1
fi

echo -e "\n${YELLOW}Removing __pycache__ directories...${NC}"
if find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null; then
    echo -e "${GREEN}Successfully removed Python cache directories.${NC}"
else
    echo -e "${RED}No __pycache__ directories found or error occurred.${NC}"
fi

echo -e "\n${YELLOW}Removing log files...${NC}"
log_files=("cleaner.log" "log.txt")
removed_logs=0

for log in "${log_files[@]}"; do
    if [ -f "$log" ]; then
        if rm -f "$log"; then
            echo -e "${GREEN}Removed: $log${NC}"
            ((removed_logs++))
        else
            echo -e "${RED}Failed to remove: $log${NC}"
        fi
    else
        echo -e "${BLUE}$log not found${NC}"
    fi
done

echo -e "${GREEN}Removed $removed_logs log file(s).${NC}"

echo -e "\n${YELLOW}Removing downloads/ and cache/ directories...${NC}"
dirs=("downloads" "cache")
removed_dirs=0

for dir in "${dirs[@]}"; do
    if [ -d "$dir" ]; then
        if rm -rf "$dir"; then
            echo -e "${GREEN}Removed directory: $dir${NC}"
            ((removed_dirs++))
        else
            echo -e "${RED}Failed to remove directory: $dir${NC}"
        fi
    else
        echo -e "${BLUE}$dir directory not found${NC}"
    fi
done

echo -e "${GREEN}Removed $removed_dirs directory(ies).${NC}"

echo -e "\n${YELLOW}Remaining files/directories:${NC}"
ls -lah --color=auto

echo -e "\n${YELLOW}Clearing RAM cache...${NC}"
if [ "$(id -u)" -ne 0 ]; then
    echo -e "${RED}Warning: Need root privileges to clear RAM cache.${NC}"
    echo -e "${BLUE}Running with sudo...${NC}"
    if sudo sync && echo 3 | sudo tee /proc/sys/vm/drop_caches >/dev/null; then
        echo -e "${GREEN}RAM cache cleared successfully.${NC}"
    else
        echo -e "${RED}Failed to clear RAM cache.${NC}"
    fi
else
    if sync && echo 3 | tee /proc/sys/vm/drop_caches >/dev/null; then
        echo -e "${GREEN}RAM cache cleared successfully.${NC}"
    else
        echo -e "${RED}Failed to clear RAM cache.${NC}"
    fi
fi

echo -e "\n${BLUE}╔══════════════════════════════════════════════╗"
echo -e "║      ${GREEN}Cleanup completed!${BLUE}       ║"
echo -e "╚══════════════════════════════════════════════╝${NC}"
