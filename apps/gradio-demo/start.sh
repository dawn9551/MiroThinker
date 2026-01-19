#!/bin/bash
# Gradio Demo 启动脚本 - 使用 Anthropic API

# 设置 LLM 配置
export DEFAULT_LLM_PROVIDER=anthropic
export DEFAULT_MODEL_NAME=claude-3-7-sonnet-20250219
export BASE_URL=https://c-z0-api-01.hash070.com
export API_KEY=sk-3IPSAHXb0F66D6da04E8T3BlBkFJ72267f9FeF0e4cE58002

# 设置 Agent 配置
export DEFAULT_AGENT_SET=mirothinker_v1.5_keep5_max400

# 设置日志目录
export LOG_DIR=logs/gradio-demo

# 启动 Gradio
echo "🚀 启动 Gradio Web UI..."
echo "📡 LLM Provider: $DEFAULT_LLM_PROVIDER"
echo "🤖 Model: $DEFAULT_MODEL_NAME"
echo "🎯 Agent: $DEFAULT_AGENT_SET"
echo ""

cd /opt/script/MiroThinker/apps/gradio-demo
uv run python main.py
