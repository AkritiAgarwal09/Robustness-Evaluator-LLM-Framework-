#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════
#  LLM Robustness Framework v2 — Local-Model Edition
# ═══════════════════════════════════════════════════════════════════
set -e
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

banner() {
  echo ""
  echo "╔══════════════════════════════════════════════════════════╗"
  echo "║   LLM Robustness & Reasoning Stability Framework  v2.0  ║"
  echo "║       Local-Model Edition  (Ollama · vLLM · LangChain)  ║"
  echo "╚══════════════════════════════════════════════════════════╝"
  echo ""
}

check_ollama() {
  if command -v ollama &>/dev/null; then
    if curl -s http://localhost:11434/api/tags &>/dev/null; then
      echo "  ✓ Ollama running — models: $(ollama list 2>/dev/null | tail -n+2 | awk '{print $1}' | tr '\n' ' ')"
    else
      echo "  ⚠  Ollama installed but NOT running → start it: ollama serve"
    fi
  else
    echo "  ⚠  Ollama not installed → https://ollama.com/install.sh"
    echo "     Then: ollama pull llama3 && ollama pull mistral"
  fi
}

setup_env() {
  [ ! -f "$PROJECT_DIR/backend/.env" ] && cp "$PROJECT_DIR/backend/.env.example" "$PROJECT_DIR/backend/.env" && echo "  ✓ Created .env — edit to configure models"
}

start_backend() {
  echo "▶ Starting API backend..."
  cd "$PROJECT_DIR/backend"
  if [ ! -d "venv" ]; then
    python3 -m venv venv && source venv/bin/activate
    pip install -q -r requirements.txt
  else
    source venv/bin/activate
  fi
  mkdir -p data
  export PYTHONPATH="$PROJECT_DIR/backend"
  uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload &
  echo $! > "$PROJECT_DIR/.backend.pid"
  echo "  ✓ API    → http://localhost:8000/docs"
}

start_frontend() {
  echo "▶ Starting React dashboard..."
  cd "$PROJECT_DIR/frontend"
  command -v npm &>/dev/null || { echo "  ✗ npm not found"; return 1; }
  [ ! -d "node_modules" ] && npm install -q
  npm start &
  echo $! > "$PROJECT_DIR/.frontend.pid"
  echo "  ✓ Dashboard → http://localhost:3000"
}

stop_all() {
  for f in .backend.pid .frontend.pid; do
    [ -f "$PROJECT_DIR/$f" ] && kill $(cat "$PROJECT_DIR/$f") 2>/dev/null; rm -f "$PROJECT_DIR/$f"
  done
  echo "✓ Stopped"
}

banner
case "${1:-start}" in
  start)
    check_ollama; echo ""; setup_env
    start_backend; sleep 2; start_frontend
    echo ""
    echo "  Dashboard   → http://localhost:3000"
    echo "  API Docs    → http://localhost:8000/docs"
    echo "  Live models → http://localhost:8000/models/live"
    echo "  Leaderboard → http://localhost:8000/leaderboard"
    echo "  Press Ctrl+C to stop"
    trap stop_all EXIT INT TERM; wait
    ;;
  stop)    stop_all ;;
  backend) check_ollama; echo ""; setup_env; start_backend; wait ;;
  ollama-setup)
    echo "▶ Pulling recommended local models..."
    ollama pull llama3 && ollama pull mistral && ollama pull phi3
    echo "✓ Done — run ./start.sh to launch"
    ;;
  *) echo "Usage: $0 [start|stop|backend|ollama-setup]" ;;
esac
