#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_DIR="${PROJECT_DIR}/.run"

stop_service() {
    local name="$1"
    local pid_file="$2"

    [[ -f "${pid_file}" ]] || {
        echo "${name} は起動していません"
        return
    }

    local pid
    pid="$(<"${pid_file}")"
    if [[ "${pid}" =~ ^[0-9]+$ ]] && kill -0 "${pid}" 2>/dev/null; then
        # start.shで作ったプロセスグループ全体を停止する。
        kill -- "-${pid}" 2>/dev/null || kill "${pid}" 2>/dev/null || true
        for _ in {1..20}; do
            kill -0 "${pid}" 2>/dev/null || break
            sleep 0.25
        done
        if kill -0 "${pid}" 2>/dev/null; then
            kill -KILL -- "-${pid}" 2>/dev/null || kill -KILL "${pid}" 2>/dev/null || true
        fi
        echo "${name} を停止しました"
    else
        echo "${name} はすでに停止しています"
    fi
    rm -f "${pid_file}"
}

stop_service "Streamlit" "${RUN_DIR}/streamlit.pid"
stop_service "vLLM" "${RUN_DIR}/vllm.pid"
