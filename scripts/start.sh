#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
MODEL_DIR="${PROJECT_DIR}/plamo-3-translate-8b-W4A16"
RUN_DIR="${PROJECT_DIR}/.run"
LOG_DIR="${PROJECT_DIR}/logs"

VLLM_PID_FILE="${RUN_DIR}/vllm.pid"
STREAMLIT_PID_FILE="${RUN_DIR}/streamlit.pid"

mkdir -p "${RUN_DIR}" "${LOG_DIR}"

read_pid() {
    local pid_file="$1"
    [[ -f "${pid_file}" ]] || return 1
    local pid
    pid="$(<"${pid_file}")"
    [[ "${pid}" =~ ^[0-9]+$ ]] || return 1
    printf '%s\n' "${pid}"
}

is_running() {
    local pid="$1"
    kill -0 "${pid}" 2>/dev/null
}

start_service() {
    local name="$1"
    local pid_file="$2"
    local log_file="$3"
    shift 3

    if local_pid="$(read_pid "${pid_file}")" && is_running "${local_pid}"; then
        echo "${name} はすでに起動しています (PID: ${local_pid})"
        return
    fi

    rm -f "${pid_file}"
    # プロセスグループを分けることで、stop.shから関連プロセスをまとめて停止する。
    setsid bash -c 'exec "$@"' bash "$@" >"${log_file}" 2>&1 &
    local_pid=$!
    printf '%s\n' "${local_pid}" >"${pid_file}"
    echo "${name} を起動しました (PID: ${local_pid})"
}

if [[ ! -d "${MODEL_DIR}" ]]; then
    echo "モデルディレクトリがありません: ${MODEL_DIR}" >&2
    echo "先にSETUP.mdのモデルダウンロード手順を実行してください。" >&2
    exit 1
fi

cd "${PROJECT_DIR}"

start_service "vLLM" "${VLLM_PID_FILE}" "${LOG_DIR}/vllm.log" \
    env VLLM_USE_FLASHINFER_SAMPLER=0 \
    uv run --with vllm --with openai --with numba vllm serve "${MODEL_DIR}" \
    --trust-remote-code \
    --served-model-name plamo-3-translate \
    --max-model-len 4096 \
    --max-num-seqs 1 \
    --gpu-memory-utilization 0.85 \
    --dtype bfloat16 \
    --enforce-eager

start_service "Streamlit" "${STREAMLIT_PID_FILE}" "${LOG_DIR}/streamlit.log" \
    uv run streamlit run app.py --server.headless true

echo
echo "起動処理を開始しました。vLLMの準備が終わるまで少し待ってください。"
echo "画面: http://localhost:8501"
echo "ログ: ${LOG_DIR}/vllm.log / ${LOG_DIR}/streamlit.log"
