"""
OFC Solver Web GUI - 基於 Streamlit 的圖形界面
"""

import streamlit as st
import requests
import json
from typing import List, Dict, Any
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
RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
SUITS = {'s': '♠', 'h': '♥', 'd': '♦', 'c': '♣'}
SUIT_COLORS = {'s': 'black', 'h': 'red', 'd': 'red', 'c': 'black'}

def card_to_display(card: Dict[str, str]) -> str:
    """將卡牌轉換為顯示格式"""
    rank = card['rank']
    suit = card['suit']
    symbol = SUITS[suit]
    color = SUIT_COLORS[suit]
    return f"<span style='color: {color}; font-size: 24px;'>{rank}{symbol}</span>"

def cards_to_string(cards: List[str]) -> str:
    """將卡牌列表轉換為字符串"""
    return " ".join(cards)

def parse_cards(cards_str: str) -> List[Dict[str, str]]:
    """解析卡牌字符串"""
    if not cards_str:
        return []
    
    cards = []
    for card in cards_str.split():
        if len(card) == 2:
            rank = card[0]
            suit = card[1]
            cards.append({"rank": rank, "suit": suit})
    return cards

def create_game_state(drawn_cards: List[Dict[str, str]], 
                     player1_cards: Dict[str, List[Dict[str, str]]],
                     player2_cards: Dict[str, List[Dict[str, str]]]) -> Dict[str, Any]:
    """創建遊戲狀態"""
    return {
        "current_round": 1,
        "players": [
            {
                "player_id": "player1",
                "top_hand": {"cards": player1_cards.get('top', []), "max_size": 3},
                "middle_hand": {"cards": player1_cards.get('middle', []), "max_size": 5},
                "bottom_hand": {"cards": player1_cards.get('bottom', []), "max_size": 5},
                "in_fantasy_land": False,
                "next_fantasy_land": False,
                "is_folded": False
            },
            {
                "player_id": "player2",
                "top_hand": {"cards": player2_cards.get('top', []), "max_size": 3},
                "middle_hand": {"cards": player2_cards.get('middle', []), "max_size": 5},
                "bottom_hand": {"cards": player2_cards.get('bottom', []), "max_size": 5},
                "in_fantasy_land": False,
                "next_fantasy_land": False,
                "is_folded": False
            }
        ],
        "current_player_index": 0,
        "drawn_cards": drawn_cards,
        "remaining_deck": []
    }

def main():
    st.title("🍍 OFC Solver GUI")
    st.markdown("### Open Face Chinese Poker 求解器圖形界面")
    
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
                    data = response.json()
                    st.json(data)
                else:
                    st.error("❌ API 連接失敗")
            except:
                st.error("❌ 無法連接到 API 服務器")
                st.info("請確保運行了: python run_api.py")
    
    # 主界面
    tab1, tab2, tab3 = st.tabs(["🎮 求解器", "📖 使用說明", "📈 歷史記錄"])
    
    with tab1:
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.header("🎴 輸入當前局面")
            
            # 當前抽到的牌
            st.subheader("當前抽到的牌")
            drawn_cards_str = st.text_input(
                "輸入格式: As Kh Qd Jc Ts", 
                placeholder="例如: As Kh Qd Jc Ts",
                help="A=Ace, K=King, Q=Queen, J=Jack, T=10, s=♠, h=♥, d=♦, c=♣"
            )
            
            # 玩家1當前牌局
            st.subheader("玩家1 當前牌局")
            p1_top = st.text_input("前墩 (最多3張)", key="p1_top")
            p1_middle = st.text_input("中墩 (最多5張)", key="p1_middle")
            p1_bottom = st.text_input("後墩 (最多5張)", key="p1_bottom")
            
            # 玩家2當前牌局
            st.subheader("玩家2 當前牌局")
            p2_top = st.text_input("前墩 (最多3張)", key="p2_top")
            p2_middle = st.text_input("中墩 (最多5張)", key="p2_middle")
            p2_bottom = st.text_input("後墩 (最多5張)", key="p2_bottom")
            
            # 求解按鈕
            if st.button("🎯 求解最佳策略", type="primary", use_container_width=True):
                if drawn_cards_str:
                    with st.spinner("正在計算最佳策略..."):
                        try:
                            # 解析輸入
                            drawn_cards = parse_cards(drawn_cards_str)
                            player1_cards = {
                                'top': parse_cards(p1_top),
                                'middle': parse_cards(p1_middle),
                                'bottom': parse_cards(p1_bottom)
                            }
                            player2_cards = {
                                'top': parse_cards(p2_top),
                                'middle': parse_cards(p2_middle),
                                'bottom': parse_cards(p2_bottom)
                            }
                            
                            # 創建遊戲狀態
                            game_state = create_game_state(drawn_cards, player1_cards, player2_cards)
                            
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
                    st.warning("請輸入當前抽到的牌")
        
        with col2:
            st.header("🎯 求解結果")
            
            if 'last_result' in st.session_state:
                result = st.session_state['last_result']
                
                # 顯示最佳動作
                st.subheader("最佳放置策略")
                move = result['move']
                if not move['is_fold']:
                    for placement in move['card_placements']:
                        card = placement['card']
                        hand = placement['hand']
                        card_display = card_to_display(card)
                        st.markdown(f"• {card_display} → **{hand}墩**", unsafe_allow_html=True)
                else:
                    st.warning("建議棄牌")
                
                # 顯示評估信息
                st.subheader("評估信息")
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    st.metric("期望分數", f"{result['evaluation']:.2f}")
                with col_b:
                    st.metric("置信度", f"{result['confidence']:.2%}")
                with col_c:
                    st.metric("計算時間", f"{result['computation_time_seconds']:.2f}秒")
                
                # 顯示前幾個選擇
                if 'top_actions' in result and result['top_actions']:
                    st.subheader("其他可選策略")
                    for i, action in enumerate(result['top_actions'][:3]):
                        st.write(f"{i+1}. 訪問次數: {action.get('visits', 0)}, "
                                f"平均獎勵: {action.get('avg_reward', 0):.2f}")
    
    with tab2:
        st.header("📖 使用說明")
        st.markdown("""
        ### 卡牌輸入格式
        - **數字牌**: 2-9 直接輸入數字
        - **10**: 輸入 T
        - **J/Q/K/A**: 直接輸入字母
        - **花色**: s=♠黑桃, h=♥紅心, d=♦方塊, c=♣梅花
        
        ### 輸入範例
        - 初始5張牌: `As Kh Qd Jc Ts`
        - 單張牌: `9h`
        - 多張牌用空格分隔: `Ah Ad Ac`
        
        ### 遊戲規則
        1. **前墩**: 最多3張牌，牌型必須最小
        2. **中墩**: 最多5張牌，牌型必須大於前墩
        3. **後墩**: 最多5張牌，牌型必須最大
        4. 違反規則會犯規（爆牌）
        
        ### 求解器設置
        - **時間限制**: 求解器計算時間上限
        - **線程數**: 並行計算的線程數量
        - **模擬次數**: MCTS 算法的模擬次數上限
        """)
    
    with tab3:
        st.header("📈 求解歷史")
        if 'history' not in st.session_state:
            st.session_state['history'] = []
        
        if st.session_state.get('history'):
            df = pd.DataFrame(st.session_state['history'])
            st.dataframe(df)
        else:
            st.info("暫無求解歷史")

if __name__ == "__main__":
    main()