"""
OFC Solver Web GUI V2 - 點擊式卡牌輸入界面
"""

import streamlit as st
import requests
import json
from typing import List, Dict, Any, Optional, Set
import pandas as pd

# 設定頁面
st.set_page_config(
    page_title="OFC Solver GUI",
    page_icon="🍍",
    layout="wide"
)

# API 配置
API_URL = "http://localhost:8000"
API_KEY = "test_key"

# 卡牌定義
RANKS = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']
SUITS = ['s', 'h', 'd', 'c']
SUIT_SYMBOLS = {'s': '♠', 'h': '♥', 'd': '♦', 'c': '♣'}
SUIT_COLORS = {'s': '#000000', 'h': '#FF0000', 'd': '#FF0000', 'c': '#000000'}

# 初始化 session state
if 'selected_cards' not in st.session_state:
    st.session_state.selected_cards = []
if 'used_cards' not in st.session_state:
    st.session_state.used_cards = set()
if 'player1_cards' not in st.session_state:
    st.session_state.player1_cards = {'top': [], 'middle': [], 'bottom': []}
if 'player2_cards' not in st.session_state:
    st.session_state.player2_cards = {'top': [], 'middle': [], 'bottom': []}
if 'current_input_target' not in st.session_state:
    st.session_state.current_input_target = 'drawn'

def card_to_string(rank: str, suit: str) -> str:
    """將卡牌轉換為字符串格式"""
    return f"{rank}{suit}"

def string_to_card(card_str: str) -> Dict[str, str]:
    """將字符串轉換為卡牌字典"""
    if len(card_str) == 2:
        return {"rank": card_str[0], "suit": card_str[1]}
    return None

def display_card(rank: str, suit: str, size: str = "medium") -> str:
    """生成卡牌的 HTML 顯示"""
    symbol = SUIT_SYMBOLS[suit]
    color = SUIT_COLORS[suit]
    card_str = card_to_string(rank, suit)
    
    sizes = {
        "small": ("40px", "60px", "16px"),
        "medium": ("50px", "70px", "20px"),
        "large": ("60px", "80px", "24px")
    }
    width, height, font_size = sizes[size]
    
    return f"""
    <div style="
        display: inline-block;
        width: {width};
        height: {height};
        border: 2px solid #333;
        border-radius: 5px;
        background: white;
        margin: 2px;
        text-align: center;
        line-height: {height};
        font-size: {font_size};
        font-weight: bold;
        color: {color};
        cursor: pointer;
        box-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    ">
        {rank}{symbol}
    </div>
    """

def is_card_used(rank: str, suit: str) -> bool:
    """檢查卡牌是否已被使用"""
    card_str = card_to_string(rank, suit)
    return card_str in st.session_state.used_cards

def add_card_to_target(rank: str, suit: str):
    """將卡牌添加到目標位置"""
    card_str = card_to_string(rank, suit)
    card_dict = {"rank": rank, "suit": suit}
    
    # 檢查是否已使用
    if is_card_used(rank, suit):
        st.error(f"卡牌 {rank}{SUIT_SYMBOLS[suit]} 已經被使用！")
        return
    
    target = st.session_state.current_input_target
    
    # 添加到對應位置
    if target == 'drawn':
        st.session_state.selected_cards.append(card_dict)
    elif target.startswith('p1_'):
        hand = target.split('_')[1]
        max_cards = 3 if hand == 'top' else 5
        if len(st.session_state.player1_cards[hand]) < max_cards:
            st.session_state.player1_cards[hand].append(card_dict)
        else:
            st.error(f"玩家1的{hand}墩已滿！")
            return
    elif target.startswith('p2_'):
        hand = target.split('_')[1]
        max_cards = 3 if hand == 'top' else 5
        if len(st.session_state.player2_cards[hand]) < max_cards:
            st.session_state.player2_cards[hand].append(card_dict)
        else:
            st.error(f"玩家2的{hand}墩已滿！")
            return
    
    # 標記為已使用
    st.session_state.used_cards.add(card_str)

def remove_card(card_dict: Dict[str, str], source: str):
    """移除卡牌"""
    card_str = card_to_string(card_dict['rank'], card_dict['suit'])
    
    if source == 'drawn':
        st.session_state.selected_cards.remove(card_dict)
    elif source.startswith('p1_'):
        hand = source.split('_')[1]
        st.session_state.player1_cards[hand].remove(card_dict)
    elif source.startswith('p2_'):
        hand = source.split('_')[1]
        st.session_state.player2_cards[hand].remove(card_dict)
    
    # 從已使用列表中移除
    st.session_state.used_cards.discard(card_str)

def clear_all():
    """清空所有選擇"""
    st.session_state.selected_cards = []
    st.session_state.player1_cards = {'top': [], 'middle': [], 'bottom': []}
    st.session_state.player2_cards = {'top': [], 'middle': [], 'bottom': []}
    st.session_state.used_cards = set()

def create_game_state() -> Dict[str, Any]:
    """創建遊戲狀態"""
    return {
        "current_round": 1,
        "players": [
            {
                "player_id": "player1",
                "top_hand": {"cards": st.session_state.player1_cards['top'], "max_size": 3},
                "middle_hand": {"cards": st.session_state.player1_cards['middle'], "max_size": 5},
                "bottom_hand": {"cards": st.session_state.player1_cards['bottom'], "max_size": 5},
                "in_fantasy_land": False,
                "next_fantasy_land": False,
                "is_folded": False
            },
            {
                "player_id": "player2",
                "top_hand": {"cards": st.session_state.player2_cards['top'], "max_size": 3},
                "middle_hand": {"cards": st.session_state.player2_cards['middle'], "max_size": 5},
                "bottom_hand": {"cards": st.session_state.player2_cards['bottom'], "max_size": 5},
                "in_fantasy_land": False,
                "next_fantasy_land": False,
                "is_folded": False
            }
        ],
        "current_player_index": 0,
        "drawn_cards": st.session_state.selected_cards,
        "remaining_deck": []
    }

def main():
    st.title("🍍 OFC Solver GUI - 點擊式界面")
    
    # 側邊欄設置
    with st.sidebar:
        st.header("⚙️ 求解器設置")
        time_limit = st.slider("時間限制（秒）", 1, 60, 10)
        threads = st.slider("線程數", 1, 8, 4)
        simulations = st.number_input("模擬次數", 1000, 1000000, 100000, step=10000)
        
        st.header("📊 API 狀態")
        if st.button("檢查連接"):
            try:
                response = requests.get(f"{API_URL}/api/v1/health")
                if response.status_code == 200:
                    st.success("✅ API 連接正常")
                else:
                    st.error("❌ API 連接失敗")
            except:
                st.error("❌ 無法連接到 API 服務器")
                st.info("請確保運行了: python run_api.py")
        
        st.divider()
        
        if st.button("🗑️ 清空所有選擇", type="secondary", use_container_width=True):
            clear_all()
            st.rerun()
    
    # 主界面
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.header("🎴 卡牌選擇器")
        
        # 選擇輸入目標
        st.subheader("選擇輸入位置")
        target_options = {
            'drawn': '📥 當前抽到的牌',
            'p1_top': '👤 玩家1 - 前墩',
            'p1_middle': '👤 玩家1 - 中墩',
            'p1_bottom': '👤 玩家1 - 後墩',
            'p2_top': '🤖 玩家2 - 前墩',
            'p2_middle': '🤖 玩家2 - 中墩',
            'p2_bottom': '🤖 玩家2 - 後墩'
        }
        
        cols = st.columns(len(target_options))
        for idx, (key, label) in enumerate(target_options.items()):
            with cols[idx]:
                if st.button(label, key=f"target_{key}", 
                           type="primary" if st.session_state.current_input_target == key else "secondary",
                           use_container_width=True):
                    st.session_state.current_input_target = key
                    st.rerun()
        
        # 顯示當前選擇的目標
        st.info(f"當前輸入到: {target_options[st.session_state.current_input_target]}")
        
        # 卡牌選擇網格
        st.subheader("點擊選擇卡牌")
        
        for suit in SUITS:
            st.write(f"**{SUIT_SYMBOLS[suit]} {suit.upper()}**")
            cols = st.columns(13)
            for idx, rank in enumerate(RANKS):
                with cols[idx]:
                    # 檢查是否已使用
                    used = is_card_used(rank, suit)
                    button_key = f"card_{rank}_{suit}"
                    
                    # 使用不同的樣式顯示已使用的卡牌
                    if used:
                        st.button(f"{rank}", key=button_key, disabled=True, use_container_width=True)
                    else:
                        if st.button(f"{rank}", key=button_key, use_container_width=True):
                            add_card_to_target(rank, suit)
                            st.rerun()
        
        # 顯示當前選擇的牌
        st.divider()
        st.subheader("📋 當前牌局狀態")
        
        # 當前抽到的牌
        st.write("**📥 當前抽到的牌:**")
        if st.session_state.selected_cards:
            card_html = ""
            for card in st.session_state.selected_cards:
                card_html += display_card(card['rank'], card['suit'], "small")
            card_html += f"<span style='margin-left: 10px;'>共 {len(st.session_state.selected_cards)} 張</span>"
            st.markdown(card_html, unsafe_allow_html=True)
            
            # 移除按鈕
            cols = st.columns(len(st.session_state.selected_cards))
            for idx, card in enumerate(st.session_state.selected_cards):
                with cols[idx]:
                    if st.button(f"❌", key=f"remove_drawn_{idx}"):
                        remove_card(card, 'drawn')
                        st.rerun()
        else:
            st.write("*未選擇*")
        
        # 玩家1的牌
        st.write("**👤 玩家1:**")
        for hand, label in [('top', '前墩'), ('middle', '中墩'), ('bottom', '後墩')]:
            cards = st.session_state.player1_cards[hand]
            max_cards = 3 if hand == 'top' else 5
            st.write(f"- {label} ({len(cards)}/{max_cards}):")
            if cards:
                card_html = ""
                for card in cards:
                    card_html += display_card(card['rank'], card['suit'], "small")
                st.markdown(card_html, unsafe_allow_html=True)
                
                # 移除按鈕
                cols = st.columns(len(cards))
                for idx, card in enumerate(cards):
                    with cols[idx]:
                        if st.button(f"❌", key=f"remove_p1_{hand}_{idx}"):
                            remove_card(card, f'p1_{hand}')
                            st.rerun()
        
        # 玩家2的牌
        st.write("**🤖 玩家2:**")
        for hand, label in [('top', '前墩'), ('middle', '中墩'), ('bottom', '後墩')]:
            cards = st.session_state.player2_cards[hand]
            max_cards = 3 if hand == 'top' else 5
            st.write(f"- {label} ({len(cards)}/{max_cards}):")
            if cards:
                card_html = ""
                for card in cards:
                    card_html += display_card(card['rank'], card['suit'], "small")
                st.markdown(card_html, unsafe_allow_html=True)
                
                # 移除按鈕
                cols = st.columns(len(cards))
                for idx, card in enumerate(cards):
                    with cols[idx]:
                        if st.button(f"❌", key=f"remove_p2_{hand}_{idx}"):
                            remove_card(card, f'p2_{hand}')
                            st.rerun()
    
    with col2:
        st.header("🎯 求解結果")
        
        # 求解按鈕
        if st.button("🎯 求解最佳策略", type="primary", use_container_width=True):
            if st.session_state.selected_cards:
                with st.spinner("正在計算最佳策略..."):
                    try:
                        game_state = create_game_state()
                        
                        # 調用 API
                        response = requests.post(
                            f"{API_URL}/api/v1/solve",
                            json={
                                "game_state": game_state,
                                "options": {
                                    "time_limit": time_limit,
                                    "threads": threads,
                                    "simulations": simulations
                                }
                            },
                            headers={"X-API-Key": API_KEY}
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            st.session_state['last_result'] = result
                            st.success("✅ 求解完成！")
                        else:
                            st.error(f"❌ 求解失敗: {response.text}")
                    except Exception as e:
                        st.error(f"❌ 錯誤: {str(e)}")
            else:
                st.warning("請先選擇當前抽到的牌")
        
        # 顯示結果
        if 'last_result' in st.session_state:
            result = st.session_state['last_result']
            
            st.subheader("最佳放置策略")
            move = result['move']
            if not move['is_fold']:
                for placement in move['card_placements']:
                    card = placement['card']
                    hand = placement['hand']
                    card_html = display_card(card['rank'], card['suit'], "large")
                    hand_name = {'top': '前墩', 'middle': '中墩', 'bottom': '後墩'}[hand]
                    st.markdown(f"{card_html} → **{hand_name}**", unsafe_allow_html=True)
            else:
                st.warning("建議棄牌")
            
            st.divider()
            
            # 評估信息
            st.subheader("評估信息")
            col_a, col_b = st.columns(2)
            with col_a:
                st.metric("期望分數", f"{result['evaluation']:.2f}")
                st.metric("置信度", f"{result['confidence']:.2%}")
            with col_b:
                st.metric("計算時間", f"{result['computation_time_seconds']:.2f}秒")
                st.metric("模擬次數", f"{result.get('simulations', 0):,}")
            
            # 統計信息
            if 'expected_score' in result:
                st.metric("期望總分", f"{result['expected_score']:.2f}")
        
        # 使用說明
        with st.expander("📖 使用說明"):
            st.markdown("""
            ### 操作步驟：
            1. **選擇輸入位置**：點擊上方按鈕選擇要輸入的位置
            2. **點擊卡牌**：在卡牌網格中點擊選擇
            3. **求解**：點擊"求解最佳策略"按鈕
            
            ### 快捷操作：
            - 灰色按鈕表示卡牌已被使用
            - 點擊 ❌ 可以移除已選擇的卡牌
            - 使用側邊欄的"清空所有選擇"重置
            
            ### 花色對照：
            - ♠ = s (黑桃)
            - ♥ = h (紅心)  
            - ♦ = d (方塊)
            - ♣ = c (梅花)
            """)

if __name__ == "__main__":
    main()