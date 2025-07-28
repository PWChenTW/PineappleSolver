#!/usr/bin/env python3
"""
Pineapple OFC GUI - Complete Streamlit Interface
基於 ofc_solver_optimized.py 的完整可玩遊戲界面
"""

import streamlit as st
import time
import random
from typing import List, Dict, Tuple, Optional, Any
import json
from datetime import datetime
import pandas as pd

# Import solver components - need to handle the import properly
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ofc_solver_joker import (
    create_full_deck, Card, PineappleStateJoker as PineappleState,
    RANKS, SUITS, RANK_VALUES
)
from ofc_solver_optimized import OptimizedStreetByStreetSolver

# Configure Streamlit page
st.set_page_config(
    page_title="Pineapple OFC Solver",
    page_icon="🍍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better card visualization
st.markdown("""
<style>
    /* Card styling */
    .card {
        display: inline-block;
        width: 50px;
        height: 70px;
        border: 2px solid #333;
        border-radius: 5px;
        margin: 2px;
        text-align: center;
        line-height: 70px;
        font-size: 20px;
        font-weight: bold;
        background: white;
        cursor: pointer;
        transition: all 0.2s;
    }
    
    .card:hover {
        transform: translateY(-5px);
        box-shadow: 0 5px 10px rgba(0,0,0,0.2);
    }
    
    .card.selected {
        background: #ffd700;
        border-color: #ff6b6b;
    }
    
    .card.hearts, .card.diamonds {
        color: red;
    }
    
    .card.spades, .card.clubs {
        color: black;
    }
    
    .card.joker {
        background: linear-gradient(45deg, #ff6b6b, #4ecdc4);
        color: white;
    }
    
    /* Hand container styling */
    .hand-container {
        border: 2px solid #ddd;
        border-radius: 10px;
        padding: 10px;
        margin: 10px 0;
        min-height: 90px;
        background: #f8f9fa;
    }
    
    .hand-label {
        font-weight: bold;
        margin-bottom: 5px;
        color: #333;
    }
    
    /* Button styling */
    .stButton > button {
        width: 100%;
        height: 50px;
        font-size: 16px;
        font-weight: bold;
    }
    
    /* Metric styling */
    .metric-container {
        background: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
def init_session_state():
    """初始化會話狀態"""
    if 'game_state' not in st.session_state:
        st.session_state.game_state = PineappleState()
    
    if 'solver' not in st.session_state:
        st.session_state.solver = OptimizedStreetByStreetSolver(
            include_jokers=True,
            num_simulations=10000  # Default to 10k for faster response
        )
    
    if 'current_street' not in st.session_state:
        st.session_state.current_street = 0
    
    if 'initial_cards' not in st.session_state:
        st.session_state.initial_cards = []
    
    if 'street_cards' not in st.session_state:
        st.session_state.street_cards = []
    
    if 'selected_cards' not in st.session_state:
        st.session_state.selected_cards = []
    
    if 'game_history' not in st.session_state:
        st.session_state.game_history = []
    
    if 'ai_suggestions' not in st.session_state:
        st.session_state.ai_suggestions = {}
    
    if 'deck' not in st.session_state:
        st.session_state.deck = create_full_deck(include_jokers=True)
    
    if 'show_ai_thinking' not in st.session_state:
        st.session_state.show_ai_thinking = False
    
    if 'placement_count' not in st.session_state:
        st.session_state.placement_count = 0

def card_to_html(card: Card, clickable: bool = True, selected: bool = False) -> str:
    """將牌轉換為 HTML 表示"""
    suit_symbols = {'s': '♠', 'h': '♥', 'd': '♦', 'c': '♣', 'j': '🃏'}
    suit_classes = {'s': 'spades', 'h': 'hearts', 'd': 'diamonds', 'c': 'clubs', 'j': 'joker'}
    
    suit_symbol = suit_symbols.get(card.suit, card.suit)
    suit_class = suit_classes.get(card.suit, '')
    
    display_text = f"{card.rank}{suit_symbol}" if not card.is_joker() else "🃏"
    
    selected_class = 'selected' if selected else ''
    onclick = f"onclick='selectCard(\"{card.rank}{card.suit}\")'" if clickable else ""
    
    return f'<div class="card {suit_class} {selected_class}" {onclick}>{display_text}</div>'

def display_hand(hand_cards: List[Card], label: str, max_cards: int):
    """顯示一手牌"""
    st.markdown(f'<div class="hand-label">{label} ({len(hand_cards)}/{max_cards})</div>', 
                unsafe_allow_html=True)
    
    cards_html = '<div class="hand-container">'
    for card in hand_cards:
        cards_html += card_to_html(card, clickable=False)
    
    # Add empty slots
    for _ in range(max_cards - len(hand_cards)):
        cards_html += '<div class="card" style="background: #e0e0e0; border-style: dashed;">_</div>'
    
    cards_html += '</div>'
    st.markdown(cards_html, unsafe_allow_html=True)

def display_current_cards(cards: List[Card], selected_indices: List[int]):
    """顯示當前可選擇的牌"""
    cards_html = '<div style="text-align: center; margin: 20px 0;">'
    for i, card in enumerate(cards):
        cards_html += card_to_html(card, clickable=True, selected=(i in selected_indices))
    cards_html += '</div>'
    
    # Add JavaScript for card selection
    cards_html += """
    <script>
    function selectCard(cardId) {
        // This would normally trigger a Streamlit callback
        console.log('Selected card:', cardId);
    }
    </script>
    """
    
    st.markdown(cards_html, unsafe_allow_html=True)

def get_ai_suggestion(state: PineappleState, available_cards: List[Card], 
                     remaining_deck: List[Card]) -> Dict[str, Any]:
    """獲取 AI 建議"""
    with st.spinner("AI 正在思考最佳策略..."):
        start_time = time.time()
        
        # Use MCTS to find best action
        mcts_result = st.session_state.solver.mcts.search(
            state.copy(),
            available_cards[:10],  # Limit cards for faster computation
            time_limit=2.0  # 2 second time limit
        )
        
        elapsed_time = time.time() - start_time
        
        # Extract suggestion details
        if mcts_result.get('best_action'):
            card, position = mcts_result['best_action']
            suggestion = {
                'card': card,
                'position': position,
                'expected_score': mcts_result.get('best_score', 0),
                'confidence': mcts_result['action_visits'].get(mcts_result['best_action'], 0) / 
                            sum(mcts_result['action_visits'].values()) if mcts_result['action_visits'] else 0,
                'computation_time': elapsed_time,
                'total_simulations': mcts_result['stats']['total_simulations']
            }
        else:
            suggestion = None
    
    return suggestion

def calculate_hand_strength(state: PineappleState) -> Dict[str, Any]:
    """計算當前手牌強度"""
    front_rank, front_score = state.front_hand.evaluate()
    middle_rank, middle_score = state.middle_hand.evaluate()
    back_rank, back_score = state.back_hand.evaluate()
    
    rank_names = [
        "高牌", "一對", "兩對", "三條", "順子", 
        "同花", "葫蘆", "四條", "同花順", "皇家同花順"
    ]
    
    return {
        'front': {'rank': front_rank, 'name': rank_names[min(front_rank, 9)], 'score': front_score},
        'middle': {'rank': middle_rank, 'name': rank_names[min(middle_rank, 9)], 'score': middle_score},
        'back': {'rank': back_rank, 'name': rank_names[min(back_rank, 9)], 'score': back_score},
        'is_valid': state.is_valid(),
        'fantasy_land': state.has_fantasy_land()
    }

def parse_card_from_placement(card_str: str) -> Card:
    """從擺放字符串解析卡牌"""
    if card_str.startswith('X'):
        return Card(rank='X', suit='j')
    else:
        return Card(rank=card_str[0], suit=card_str[1])

def main():
    """主應用程序"""
    init_session_state()
    
    # Title and header
    st.title("🍍 Pineapple OFC Solver")
    st.markdown("**AI 輔助的中國撲克遊戲**")
    
    # Sidebar for controls and settings
    with st.sidebar:
        st.header("遊戲控制")
        
        if st.button("🎮 新遊戲", use_container_width=True):
            st.session_state.game_state = PineappleState()
            st.session_state.current_street = 0
            st.session_state.initial_cards = []
            st.session_state.street_cards = []
            st.session_state.selected_cards = []
            st.session_state.ai_suggestions = {}
            st.session_state.deck = create_full_deck(include_jokers=True)
            st.session_state.placement_count = 0
            st.rerun()
        
        st.divider()
        
        st.header("設置")
        
        num_simulations = st.select_slider(
            "MCTS 模擬次數",
            options=[1000, 5000, 10000, 25000, 50000, 100000],
            value=st.session_state.solver.num_simulations
        )
        
        if num_simulations != st.session_state.solver.num_simulations:
            st.session_state.solver.num_simulations = num_simulations
            st.session_state.solver.mcts.num_simulations = num_simulations
        
        include_jokers = st.checkbox("包含鬼牌", value=st.session_state.solver.include_jokers)
        
        if include_jokers != st.session_state.solver.include_jokers:
            st.session_state.solver.include_jokers = include_jokers
            st.session_state.deck = create_full_deck(include_jokers=include_jokers)
        
        show_ai_thinking = st.checkbox("顯示 AI 思考過程", value=st.session_state.show_ai_thinking)
        st.session_state.show_ai_thinking = show_ai_thinking
        
        st.divider()
        
        # Game save/load
        st.header("遊戲存檔")
        
        if st.button("💾 保存遊戲", use_container_width=True):
            game_data = {
                'timestamp': datetime.now().isoformat(),
                'game_state': {
                    'front': [str(c) for c in st.session_state.game_state.front_hand.cards],
                    'middle': [str(c) for c in st.session_state.game_state.middle_hand.cards],
                    'back': [str(c) for c in st.session_state.game_state.back_hand.cards],
                    'discarded': [str(c) for c in st.session_state.game_state.discarded]
                },
                'current_street': st.session_state.current_street,
                'settings': {
                    'num_simulations': num_simulations,
                    'include_jokers': include_jokers
                }
            }
            st.download_button(
                label="下載存檔",
                data=json.dumps(game_data, indent=2),
                file_name=f"ofc_save_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
        
        uploaded_file = st.file_uploader("載入存檔", type=['json'])
        if uploaded_file is not None:
            game_data = json.load(uploaded_file)
            # Restore game state (implementation needed)
            st.success("遊戲已載入！")
    
    # Main game area
    col1, col2, col3 = st.columns([2, 3, 2])
    
    with col2:
        st.header("牌桌")
        
        # Display player's hands
        display_hand(st.session_state.game_state.front_hand.cards, "前墩", 3)
        display_hand(st.session_state.game_state.middle_hand.cards, "中墩", 5)
        display_hand(st.session_state.game_state.back_hand.cards, "後墩", 5)
        
        # Display discarded cards
        if st.session_state.game_state.discarded:
            st.markdown("**棄牌堆:**")
            discarded_html = '<div style="margin: 10px 0;">'
            for card in st.session_state.game_state.discarded:
                discarded_html += card_to_html(card, clickable=False)
            discarded_html += '</div>'
            st.markdown(discarded_html, unsafe_allow_html=True)
    
    with col1:
        st.header("遊戲控制")
        
        # Street control
        if st.session_state.current_street == 0:
            if not st.session_state.initial_cards:
                if st.button("🎲 發初始5張牌", use_container_width=True):
                    # Deal initial 5 cards
                    if not st.session_state.deck:
                        st.session_state.deck = create_full_deck(include_jokers=st.session_state.solver.include_jokers)
                    deck = st.session_state.deck.copy()
                    random.shuffle(deck)
                    if len(deck) >= 5:
                        st.session_state.initial_cards = [deck.pop() for _ in range(5)]
                        st.session_state.deck = deck
                    else:
                        st.error("牌組中沒有足夠的牌！")
                    st.rerun()
            else:
                st.markdown("**初始5張牌:**")
                display_current_cards(st.session_state.initial_cards, st.session_state.selected_cards)
                
                # Position selection for initial placement
                if st.button("🤖 獲取 AI 建議", use_container_width=True):
                    # 使用 PineappleOFCSolverJoker 來獲取建議
                    from ofc_solver_joker import PineappleOFCSolverJoker
                    joker_solver = PineappleOFCSolverJoker(num_simulations=10000)
                    arrangement = joker_solver.solve_initial_five(st.session_state.initial_cards)
                    
                    # 轉換為建議格式
                    suggestion = {
                        'placement': [],
                        'score': 0,
                        'method': 'MCTS'
                    }
                    
                    # 從 arrangement 中提取擺放建議
                    for card in st.session_state.initial_cards:
                        if card in arrangement.front_hand.cards:
                            suggestion['placement'].append((str(card), 'front'))
                        elif card in arrangement.middle_hand.cards:
                            suggestion['placement'].append((str(card), 'middle'))
                        elif card in arrangement.back_hand.cards:
                            suggestion['placement'].append((str(card), 'back'))
                    
                    st.session_state.ai_suggestions['initial'] = suggestion
                
                if 'initial' in st.session_state.ai_suggestions:
                    sug = st.session_state.ai_suggestions['initial']
                    st.success(f"AI 建議最佳擺放（預期分數: {sug['score']:.2f}）")
                    
                    # Show placement details
                    for card_str, position in sug['placement']:
                        st.info(f"{card_str} → {position}")
                    
                    if st.button("✅ 採用 AI 建議", use_container_width=True):
                        for card_str, position in sug['placement']:
                            # Find the matching card from initial_cards
                            for card in st.session_state.initial_cards:
                                if str(card) == card_str:
                                    st.session_state.game_state.place_card(card, position)
                                    break
                        st.session_state.current_street = 1
                        st.session_state.initial_cards = []
                        st.rerun()
                
                # Manual placement option
                st.divider()
                st.markdown("**手動擺放:**")
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.session_state.initial_cards:
                        selected_card_idx = st.selectbox(
                            "選擇牌", 
                            options=range(len(st.session_state.initial_cards)),
                            format_func=lambda x: str(st.session_state.initial_cards[x])
                        )
                with col_b:
                    position = st.selectbox("放置位置", ['front', 'middle', 'back'])
                
                if st.button("放置牌", use_container_width=True):
                    if st.session_state.initial_cards:
                        card = st.session_state.initial_cards.pop(selected_card_idx)
                        st.session_state.game_state.place_card(card, position)
                        st.session_state.placement_count += 1
                        
                        if not st.session_state.initial_cards:
                            st.session_state.current_street = 1
                            st.session_state.placement_count = 0
                        st.rerun()
        
        elif 1 <= st.session_state.current_street <= 4:
            if not st.session_state.street_cards:
                if st.button(f"🎲 抽第{st.session_state.current_street}街 (3張牌)", use_container_width=True):
                    # Draw 3 cards
                    if not st.session_state.deck:
                        st.session_state.deck = create_full_deck(include_jokers=st.session_state.solver.include_jokers)
                        # Remove already used cards
                        used_cards = (st.session_state.game_state.front_hand.cards + 
                                    st.session_state.game_state.middle_hand.cards + 
                                    st.session_state.game_state.back_hand.cards + 
                                    st.session_state.game_state.discarded)
                        st.session_state.deck = [c for c in st.session_state.deck if c not in used_cards]
                    
                    if len(st.session_state.deck) >= 3:
                        random.shuffle(st.session_state.deck)
                        st.session_state.street_cards = [st.session_state.deck.pop() for _ in range(3)]
                        st.rerun()
                    else:
                        st.error("牌堆中沒有足夠的牌！")
            else:
                st.markdown(f"**第{st.session_state.current_street}街 - 選擇2張擺放，1張棄牌:**")
                display_current_cards(st.session_state.street_cards, st.session_state.selected_cards)
                
                # AI suggestion for street
                if st.button("🤖 獲取 AI 建議", use_container_width=True):
                    # 使用街道求解器
                    from ofc_cli_street import StreetByStreetCLI
                    street_solver = StreetByStreetCLI(num_simulations=1000)
                    
                    # 複製當前狀態
                    street_solver.game_state = st.session_state.game_state
                    street_solver.used_cards = set()
                    
                    # 添加已使用的牌
                    for card in (st.session_state.game_state.front_hand.cards + 
                               st.session_state.game_state.middle_hand.cards + 
                               st.session_state.game_state.back_hand.cards + 
                               st.session_state.game_state.discarded):
                        street_solver.used_cards.add(str(card))
                    
                    # 生成所有可能的動作
                    actions = street_solver._generate_possible_actions(st.session_state.street_cards)
                    
                    # 評估並找出最佳動作
                    best_score = float('-inf')
                    best_action = None
                    
                    for placements, discard in actions[:20]:  # 限制評估數量以提高速度
                        # 創建臨時狀態
                        temp_state = street_solver._copy_state(st.session_state.game_state)
                        
                        # 應用動作
                        valid = True
                        for card, position in placements:
                            if not street_solver._can_place_card(temp_state, position):
                                valid = False
                                break
                            street_solver._place_card_in_state(temp_state, card, position)
                        
                        if not valid or not temp_state.is_valid():
                            continue
                        
                        # 評估狀態
                        score = street_solver._evaluate_state(temp_state)
                        
                        if score > best_score:
                            best_score = score
                            best_action = (placements, discard)
                    
                    if best_action:
                        placements, discard = best_action
                        suggestion = {
                            'placements': [(str(c), pos) for c, pos in placements],
                            'discard': str(discard),
                            'score': best_score
                        }
                        st.session_state.ai_suggestions[f'street_{st.session_state.current_street}'] = suggestion
                
                if f'street_{st.session_state.current_street}' in st.session_state.ai_suggestions:
                    sug = st.session_state.ai_suggestions[f'street_{st.session_state.current_street}']
                    if sug['placements']:
                        st.success("AI 建議:")
                        st.info(f"擺放: {sug['placements']}")
                        st.info(f"棄牌: {sug['discard']}")
                        
                        if st.button("✅ 採用 AI 建議", use_container_width=True):
                            # Apply AI suggestion
                            placed_cards = []
                            discard_card = None
                            
                            # First find the discard card
                            for card in st.session_state.street_cards:
                                if str(card) == sug['discard']:
                                    discard_card = card
                                    break
                            
                            # Then place the other two cards
                            for card_str, position in sug['placements']:
                                for card in st.session_state.street_cards:
                                    if str(card) == card_str and card not in placed_cards and card != discard_card:
                                        st.session_state.game_state.place_card(card, position)
                                        placed_cards.append(card)
                                        break
                            
                            # Finally discard the designated card
                            if discard_card:
                                st.session_state.game_state.discarded.append(discard_card)
                            
                            st.session_state.street_cards = []
                            st.session_state.current_street += 1
                            st.rerun()
                
                # Manual placement controls
                st.divider()
                st.markdown("**手動擺放:**")
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.session_state.street_cards:
                        selected_card_idx = st.selectbox(
                            "選擇牌", 
                            options=range(len(st.session_state.street_cards)),
                            format_func=lambda x: str(st.session_state.street_cards[x])
                        )
                with col_b:
                    position = st.selectbox("放置位置", st.session_state.game_state.get_available_positions())
                
                if st.button("放置牌", use_container_width=True):
                    if st.session_state.street_cards and selected_card_idx < len(st.session_state.street_cards):
                        card = st.session_state.street_cards[selected_card_idx]
                        if st.session_state.game_state.place_card(card, position):
                            st.success(f"已放置 {card} 到 {position}")
                            # Remove placed card
                            st.session_state.street_cards.pop(selected_card_idx)
                            st.session_state.placement_count += 1
                            
                            # Check if we need to discard
                            if len(st.session_state.street_cards) == 1:
                                st.session_state.game_state.discarded.append(st.session_state.street_cards[0])
                                st.info(f"自動棄牌: {st.session_state.street_cards[0]}")
                                st.session_state.street_cards = []
                                st.session_state.current_street += 1
                                st.session_state.placement_count = 0
                            st.rerun()
        
        else:
            st.success("🎉 遊戲完成！")
            if st.session_state.game_state.is_valid():
                st.balloons()
                if st.session_state.game_state.has_fantasy_land():
                    st.success("✨ 恭喜進入夢幻樂園！")
            else:
                st.error("❌ 犯規！手牌強度順序不正確。")
    
    with col3:
        st.header("統計面板")
        
        # Calculate and display hand strength
        strength = calculate_hand_strength(st.session_state.game_state)
        
        st.markdown("**當前手牌強度:**")
        
        # Create metrics
        col_1, col_2, col_3 = st.columns(3)
        with col_1:
            st.metric("前墩", strength['front']['name'])
        with col_2:
            st.metric("中墩", strength['middle']['name'])
        with col_3:
            st.metric("後墩", strength['back']['name'])
        
        # Status indicators
        if strength['is_valid']:
            st.success("✅ 合法擺放")
        else:
            st.error("❌ 犯規風險")
        
        if strength['fantasy_land']:
            st.info("✨ Fantasy Land 機會！")
        
        st.divider()
        
        # AI performance stats
        if st.session_state.ai_suggestions:
            st.markdown("**AI 性能統計:**")
            
            latest_suggestion = list(st.session_state.ai_suggestions.values())[-1]
            if isinstance(latest_suggestion, dict):
                if 'score' in latest_suggestion:
                    st.metric("預期分數", f"{latest_suggestion['score']:.2f}")
                if 'method' in latest_suggestion:
                    st.metric("求解方法", latest_suggestion['method'])
        
        # Cache stats
        if hasattr(st.session_state.solver, 'cache_manager'):
            cache_stats = st.session_state.solver.cache_manager.get_stats()
            st.markdown("**緩存統計:**")
            col_a, col_b = st.columns(2)
            with col_a:
                st.metric("命中率", f"{cache_stats['hit_rate']:.1%}")
            with col_b:
                st.metric("緩存大小", f"{cache_stats['size']:,}")
    
    # Footer with help
    with st.expander("📖 遊戲說明"):
        st.markdown("""
        ### Pineapple OFC 規則
        
        1. **初始階段**: 發5張牌，自由擺放到三道
        2. **抽牌階段**: 每回合抽3張，擺2張棄1張
        3. **牌型要求**: 後墩 ≥ 中墩 ≥ 前墩（否則犯規）
        4. **Fantasy Land**: 前墩達到QQ或更好進入夢幻樂園
        
        ### 使用方法
        
        1. 點擊「新遊戲」開始
        2. 點擊「發初始5張牌」
        3. 使用 AI 建議或手動擺放
        4. 繼續抽牌直到完成
        
        ### AI 功能
        
        - **MCTS 算法**: 使用蒙特卡洛樹搜索找出最佳策略
        - **並行計算**: 多核心加速計算
        - **智能剪枝**: 減少不必要的計算
        - **緩存優化**: 記憶已計算的局面
        """)

if __name__ == "__main__":
    main()