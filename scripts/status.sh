#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_DIR="${PROJECT_DIR}/.run"

show_status() {
    local name="$1"
    local pid_file="$2"
    if [[ -f "${pid_file}" ]]; then
        local pid
        pid="$(<"${pid_file}")"
        if [[ "${pid}" =~ ^[0-9]+$ ]] && kill -0 "${pid}" 2>/dev/null; then
            echo "${name}: 起動中 (PID: ${pid})"
            return
        fi
    fi
    echo "${name}: 停止中"
}

show_status "vLLM" "${RUN_DIR}/vllm.pid"
show_status "Streamlit" "${RUN_DIR}/streamlit.pid"
