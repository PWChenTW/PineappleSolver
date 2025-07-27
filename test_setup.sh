#!/bin/bash

# 通用AI協作開發模板 - 環境測試腳本
# 測試設置是否正確完成

echo "🧪 開始測試通用AI協作開發環境..."

# 檢查基本目錄結構
echo "📁 檢查目錄結構..."
REQUIRED_DIRS=(
    ".claude/agents"
    ".claude/commands" 
    ".claude/scheduler"
    ".kiro/steering"
    ".kiro/specs"
    "docs/quick_reference"
    "src/domain"
    "tests/behavior"
    "scripts/monitoring"
)

MISSING_DIRS=()
for dir in "${REQUIRED_DIRS[@]}"; do
    if [ ! -d "$dir" ]; then
        MISSING_DIRS+=("$dir")
    fi
done

if [ ${#MISSING_DIRS[@]} -eq 0 ]; then
    echo "✅ 目錄結構完整"
else
    echo "❌ 缺少目錄: ${MISSING_DIRS[*]}"
fi

# 檢查Sub Agents配置
echo "🤖 檢查Sub Agents..."
AGENTS=(
    "business-analyst"
    "architect"
    "data-specialist"
    "integration-specialist"
    "test-engineer"
)

MISSING_AGENTS=()
for agent in "${AGENTS[@]}"; do
    if [ ! -f ".claude/agents/$agent.md" ]; then
        MISSING_AGENTS+=("$agent")
    fi
done

if [ ${#MISSING_AGENTS[@]} -eq 0 ]; then
    echo "✅ Sub Agents配置完整"
else
    echo "❌ 缺少Agent: ${MISSING_AGENTS[*]}"
fi

# 檢查Slash Commands
echo "⚡ 檢查Slash Commands..."
COMMANDS=(
    "spec-init"
    "spec-requirements"
    "spec-design"
    "spec-tasks"
)

MISSING_COMMANDS=()
for cmd in "${COMMANDS[@]}"; do
    if [ ! -f ".claude/commands/$cmd.md" ]; then
        MISSING_COMMANDS+=("$cmd")
    fi
done

if [ ${#MISSING_COMMANDS[@]} -eq 0 ]; then
    echo "✅ Slash Commands配置完整"
else
    echo "❌ 缺少Command: ${MISSING_COMMANDS[*]}"
fi

# 檢查Hooks配置
echo "🪝 檢查Hooks配置..."
if [ -f ".claude/settings.json" ]; then
    # 簡單檢查JSON格式
    if python3 -m json.tool .claude/settings.json >/dev/null 2>&1; then
        echo "✅ Hooks配置格式正確"
    else
        echo "❌ Hooks配置JSON格式錯誤"
    fi
else
    echo "❌ 缺少Hooks配置文件"
fi

# 檢查核心配置文件
echo "📄 檢查核心配置..."
CORE_FILES=(
    "CLAUDE.md"
    "README.md"
    "setup.sh"
)

MISSING_FILES=()
for file in "${CORE_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        MISSING_FILES+=("$file")
    fi
done

if [ ${#MISSING_FILES[@]} -eq 0 ]; then
    echo "✅ 核心配置文件完整"
else
    echo "❌ 缺少配置文件: ${MISSING_FILES[*]}"
fi

# 檢查Python環境
echo "🐍 檢查Python環境..."
if command -v python3 &> /dev/null; then
    echo "✅ Python3已安裝"
    
    # 檢查必要的Python模組
    PYTHON_MODULES=("json" "os" "datetime" "logging")
    for module in "${PYTHON_MODULES[@]}"; do
        if python3 -c "import $module" 2>/dev/null; then
            echo "✅ Python模組 $module 可用"
        else
            echo "❌ Python模組 $module 不可用"
        fi
    done
else
    echo "❌ Python3未安裝"
fi

# 檢查Git環境
echo "🔄 檢查Git環境..."
if command -v git &> /dev/null; then
    echo "✅ Git已安裝"
    
    if [ -d ".git" ]; then
        echo "✅ Git倉庫已初始化"
    else
        echo "⚠️  Git倉庫未初始化 (非必須)"
    fi
else
    echo "❌ Git未安裝"
fi

# 測試調度器
echo "📅 測試任務調度器..."
if [ -f ".claude/scheduler/spec_scheduler.py" ]; then
    python3 -c "
import sys
sys.path.append('.claude/scheduler')
try:
    import spec_scheduler
    print('✅ 調度器模組可導入')
except Exception as e:
    print('❌ 調度器模組錯誤:', str(e))
"
else
    echo "❌ 調度器文件不存在"
fi

# 測試品質檢查
echo "🔍 測試品質檢查..."
if [ -f ".claude/scheduler/quality_check.py" ]; then
    if python3 .claude/scheduler/quality_check.py 2>/dev/null; then
        echo "✅ 品質檢查腳本正常"
    else
        echo "⚠️  品質檢查腳本需要調整"
    fi
else
    echo "❌ 品質檢查腳本不存在"
fi

# 測試監控腳本
echo "📊 測試監控功能..."
if [ -f "scripts/monitoring/view_command_audit.py" ]; then
    if python3 scripts/monitoring/view_command_audit.py --test 2>/dev/null; then
        echo "✅ 命令審計腳本正常"
    else
        echo "⚠️  命令審計腳本需要調整"
    fi
else
    echo "❌ 命令審計腳本不存在"
fi

# 檢查知識庫文件
echo "📚 檢查知識庫..."
KNOWLEDGE_FILES=(
    ".kiro/steering/product.md"
    ".kiro/steering/tech.md"
    ".kiro/steering/methodology.md"
    ".kiro/steering/collaboration.md"
)

MISSING_KB=()
for file in "${KNOWLEDGE_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        MISSING_KB+=("$file")
    fi
done

if [ ${#MISSING_KB[@]} -eq 0 ]; then
    echo "✅ 知識庫文件完整"
else
    echo "❌ 缺少知識庫文件: ${MISSING_KB[*]}"
fi

# 整體評估
echo ""
echo "🎯 測試結果總結:"

TOTAL_CHECKS=10
PASSED_CHECKS=0

# 簡化評估邏輯
if [ ${#MISSING_DIRS[@]} -eq 0 ]; then ((PASSED_CHECKS++)); fi
if [ ${#MISSING_AGENTS[@]} -eq 0 ]; then ((PASSED_CHECKS++)); fi
if [ ${#MISSING_COMMANDS[@]} -eq 0 ]; then ((PASSED_CHECKS++)); fi
if [ -f ".claude/settings.json" ]; then ((PASSED_CHECKS++)); fi
if [ ${#MISSING_FILES[@]} -eq 0 ]; then ((PASSED_CHECKS++)); fi
if command -v python3 &> /dev/null; then ((PASSED_CHECKS++)); fi
if command -v git &> /dev/null; then ((PASSED_CHECKS++)); fi
if [ -f ".claude/scheduler/spec_scheduler.py" ]; then ((PASSED_CHECKS++)); fi
if [ -f ".claude/scheduler/quality_check.py" ]; then ((PASSED_CHECKS++)); fi
if [ ${#MISSING_KB[@]} -eq 0 ]; then ((PASSED_CHECKS++)); fi

if [ $PASSED_CHECKS -eq $TOTAL_CHECKS ]; then
    echo "🎉 所有測試通過！環境設置完美！"
    echo ""
    echo "🚀 準備就緒："
    echo "• 運行 'claude-code' 開始開發"
    echo "• 使用 '/spec-init [功能名稱] [描述]' 創建功能"
    echo "• 查看 README.md 了解更多信息"
    exit 0
elif [ $PASSED_CHECKS -gt $((TOTAL_CHECKS * 2 / 3)) ]; then
    echo "✅ 大部分測試通過，環境基本可用"
    echo "⚠️  建議修復上述警告項目以獲得最佳體驗"
    echo ""
    echo "💡 快速修復："
    echo "• 運行 './setup.sh' 自動修復大部分問題"
    echo "• 檢查Python和Git是否正確安裝"
    exit 0
else
    echo "❌ 多個關鍵測試失敗，請檢查設置"
    echo "💡 建議操作："
    echo "• 重新運行 './setup.sh' 進行修復"
    echo "• 確保Python3和Git已正確安裝"
    echo "• 檢查文件權限是否正確"
    exit 1
fi