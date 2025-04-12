#!/bin/bash
set -eo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

check_resources() {
    local REQUIRED_CPU=2
    local REQUIRED_RAM=2000
    local REQUIRED_DISK=500
    
    log_info "Checking system resources..."
    
    local CPU_CORES=$(nproc)
    [ "$CPU_CORES" -lt "$REQUIRED_CPU" ] && 
        log_warning "Insufficient CPU cores ($CPU_CORES available, $REQUIRED_CPU recommended)" ||
        log_success "CPU cores: $CPU_CORES (minimum $REQUIRED_CPU)"
    
    local RAM_AVAILABLE=$(free -m | awk '/Mem:/ {print $2}')
    [ "$RAM_AVAILABLE" -lt "$REQUIRED_RAM" ] && 
        log_warning "Insufficient RAM ($RAM_AVAILABLE MB available, $REQUIRED_RAM MB recommended)" ||
        log_success "RAM available: $RAM_AVAILABLE MB (minimum $REQUIRED_RAM MB)"
    
    local DISK_AVAILABLE=$(df -m . | awk 'NR==2 {print $4}')
    [ "$DISK_AVAILABLE" -lt "$REQUIRED_DISK" ] && 
        log_warning "Insufficient disk space ($DISK_AVAILABLE MB available, $REQUIRED_DISK MB recommended)" ||
        log_success "Disk space: $DISK_AVAILABLE MB (minimum $REQUIRED_DISK MB)"
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" >&2
}

start_opus_service() {
    while true; do
        log_info "ꜱᴛᴀʀᴛɪɴɢ ᴠx ᴀɪ ᴄᴏʀᴇ ᴇɴɢɪɴᴇ..."
        python3 -m Opus &
        VX_PID=$!
        wait $VX_PID
        log_warning "ᴠx ᴀɪ ᴄᴏʀᴇ ᴇɴɢɪɴᴇ ꜱᴛᴏᴘᴘᴇᴅ, ʀᴇꜱᴛᴀʀᴛɪɴɢ ɪɴ 5 ꜱᴇᴄᴏɴᴅꜱ..."
        sleep 5
    done
}

monitor_processes() {
    while true; do
        if ! kill -0 $GUNICORN_PID 2>/dev/null; then
            log_error "ɢᴜɴɪᴄᴏʀɴ ᴘʀᴏᴄᴇꜱꜱ ꜱᴛᴏᴘᴘᴇᴅ!"
            return 1
        fi
        sleep 10
    done
}

optimize_system() {
    log_info "ᴏᴘᴛɪᴍɪᴢɪɴɢ ꜱʏꜱᴛᴇᴍ ᴘᴇʀꜰᴏʀᴍᴀɴᴄᴇ..."
    ulimit -n 65536 2>/dev/null || log_warning "ᴄᴏᴜʟᴅ ɴᴏᴛ ɪɴᴄʀᴇᴀꜱᴇ ꜰɪʟᴇ ᴅᴇꜱᴄʀɪᴘᴛᴏʀ ʟɪᴍɪᴛ"
    sysctl -w net.core.somaxconn=65535 2>/dev/null || log_warning "ᴄᴏᴜʟᴅ ɴᴏᴛ ᴀᴅᴊᴜꜱᴛ ɴᴇᴛ.ᴄᴏʀᴇ.ꜱᴏᴍᴀxᴄᴏɴɴ"
    sysctl -w net.ipv4.tcp_max_syn_backlog=65535 2>/dev/null || log_warning "ᴄᴏᴜʟᴅ ɴᴏᴛ ᴀᴅᴊᴜꜱᴛ ᴛᴄᴘ_ᴍᴀx_ꜱʏɴ_ʙᴀᴄᴋʟᴏɢ"
}

start_services() {
    PORT=${PORT:-8080}
    WORKERS=${WORKERS:-$(( $(nproc) * 2 + 1 ))}
    
    check_resources
    optimize_system
    
    log_info "ꜱᴛᴀʀᴛɪɴɢ ᴠx ᴀɪ ᴀᴘɪ ꜱᴇʀᴠᴇʀ ᴡɪᴛʜ ɢᴜɴɪᴄᴏʀɴ ($WORKERS ᴡᴏʀᴋᴇʀꜱ)..."
    gunicorn -w $WORKERS -b 0.0.0.0:${PORT} boot:create_app \
        --access-logfile - \
        --error-logfile - \
        --worker-class gevent \
        --timeout 120 \
        --keep-alive 5 \
        --max-requests 1000 \
        --max-requests-jitter 100 &
    GUNICORN_PID=$!
    log_success "ᴠx ᴀᴘɪ ꜱᴇʀᴠᴇʀ ʀᴜɴɴɪɴɢ ᴏɴ ᴘᴏʀᴛ $PORT (PID: $GUNICORN_PID)"

    start_opus_service &
    OPUS_MONITOR_PID=$!
    
    monitor_processes &
    MONITOR_PID=$!
    
    wait $GUNICORN_PID || {
        log_error "ɢᴜɴɪᴄᴏʀɴ ꜱᴇʀᴠɪᴄᴇ ꜱᴛᴏᴘᴘᴇᴅ ᴜɴᴇxᴘᴇᴄᴛᴇᴅʟʏ"
        kill $OPUS_MONITOR_PID $MONITOR_PID 2>/dev/null
        exit 1
    }
}

shutdown_handler() {
    log_warning "ʀᴇᴄᴇɪᴠᴇᴅ ꜱʜᴜᴛᴅᴏᴡɴ ꜱɪɢɴᴀʟ, ᴛᴇʀᴍɪɴᴀᴛɪɴɢ ᴘʀᴏᴄᴇꜱꜱᴇꜱ..."
    kill -TERM $GUNICORN_PID $OPUS_MONITOR_PID $MONITOR_PID 2>/dev/null || true
    exit 0
}

trap shutdown_handler SIGINT SIGTERM SIGHUP

start_services
