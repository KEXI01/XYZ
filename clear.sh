#!/bin/bash

set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[0;33m'
BLUE='\033[0;34m'; MAGENTA='\033[0;35m'; CYAN='\033[0;36m'
BOLD='\033[1m'; NC='\033[0m'

CHECK="${GREEN}✓${NC}"
CROSS="${RED}✗${NC}"
WARN="${YELLOW}⚠${NC}"
INFO="${CYAN}ℹ${NC}"
ARROW="${BLUE}➜${NC}"

section() {
    echo -e "\n${MAGENTA}${BOLD}»»» $1 «««${NC}"
}

status() {
    [[ $2 -eq 0 ]] && echo -e "${CHECK} ${GREEN}$1${NC}" || echo -e "${CROSS} ${RED}$1${NC}"
}

clean_logs() {
    section "Log File Cleanup"
    sudo journalctl --vacuum-size=100M && status "Journal logs reduced" $?
    sudo find /var/log -type f -name "*.gz" -delete && status "Compressed logs deleted" $?
    sudo find /var/log -type f -name "*.old" -delete && status "Old logs deleted" $?
}

disk_analysis() {
    section "Disk Usage Analysis"

    echo -e "\n${ARROW} ${BOLD}Top 10 Largest Files/Dirs:${NC}"
    sudo du -ahx / 2>/dev/null | sort -rh | head -n 10 || echo -e "${WARN} Unable to analyze disk"

    echo -e "\n${ARROW} ${BOLD}Disk Space Usage:${NC}"
    df -h || echo -e "${WARN} Failed to display disk usage"

    echo -e "\n${ARROW} ${BOLD}Largest Directories in Root:/ ${NC}"
    sudo du -sh /* 2>/dev/null | sort -rh | head -n 10
}

manage_caches() {
    section "Memory & Cache Management"

    sudo sync
    echo 3 | sudo tee /proc/sys/vm/drop_caches >/dev/null && status "Caches dropped" $?

    if grep -q '^/swap' /proc/swaps; then
        sudo swapoff -a && sudo swapon -a && status "Swap reset" $?
    else
        echo -e "${WARN} No swap file configured"
    fi

    echo -e "\n${ARROW} ${BOLD}Memory Status:${NC}"
    free -h || echo -e "${WARN} Memory check failed"
}

cpu_optimization() {
    section "CPU Optimization"

    echo -e "${ARROW} ${BOLD}CPU Frequency:${NC}"
    grep "MHz" /proc/cpuinfo | sort -u || echo -e "${WARN} Can't fetch CPU frequency"

    if command -v cpupower &>/dev/null; then
        sudo cpupower frequency-set -g performance && status "Set CPU governor to performance" $?
    else
        echo -e "${WARN} cpupower not found — skipping governor tweak"
    fi
}

system_info() {
    section "System Information"
    echo -e "${ARROW} Hostname: $(hostname)"
    echo -e "${ARROW} Uptime: $(uptime -p)"
    echo -e "${ARROW} OS: $(lsb_release -d 2>/dev/null | cut -f2- || uname -a)"
    echo -e "${ARROW} Kernel: $(uname -r)"
    echo -e "${ARROW} CPU: $(lscpu | grep 'Model name' | cut -d ':' -f2 | xargs)"
    echo -e "${ARROW} Memory: $(free -h | awk '/Mem:/ {print $3 "/" $2}')"
    echo -e "${ARROW} Load Avg: $(awk '{print $1", "$2", "$3}' /proc/loadavg)"
}

main() {
    clear
    echo -e "${GREEN}${BOLD}"
    echo "╔═══════════════════════════════════════════════╗"
    echo "║        SYSTEM CLEANUP & OPTIMIZATION          ║"
    echo "║                OPUS V2.0                      ║"
    echo "╚═══════════════════════════════════════════════╝"
    echo -e "${NC}"

    system_info
    clean_logs
    manage_caches
    disk_analysis
    cpu_optimization

    echo -e "\n${GREEN}${BOLD}"
    echo "╔═══════════════════════════════════════════════╗"
    echo "║            ALL TASKS COMPLETED                ║"
    echo "╚═══════════════════════════════════════════════╝"
    echo -e "${NC}"

    echo -e "${ARROW} ${BOLD}Final System Snapshot:${NC}"
    system_info
}

main