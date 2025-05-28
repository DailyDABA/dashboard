# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import calendar
from datetime import datetime
import os
from matplotlib.font_manager import FontProperties

# ===== 必須最先設定頁面配置 =====
# 先獲取使用者參數來設定頁面標題
query_params = st.query_params
selected_user = query_params.get('user', 'User')
st.set_page_config(page_title=f"{selected_user}用戶4月儀表板", layout="wide")

# 設定基本參數
month = 4
year = 2025
base_url = "http://localhost:8501"  # 換成你的正式網址

# 假設字體檔案放在 fonts/NotoSansTC-Regular.ttf
font = FontProperties(fname='fonts/NotoSansTC-Regular.ttf')

@st.cache_data
def load_data():
    """載入資料"""
    df = pd.read_csv('data.csv')
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    df_apr = df[(df['Month'] == month) & (df['Timestamp'].dt.year == year)]
    return df_apr

@st.cache_data
def generate_user_urls():
    """產生並儲存每位使用者的專屬網址"""
    df = pd.read_csv('data.csv')
    user_ids = df['User_id'].unique().tolist()
    
    user_url_list = []
    for user_id in user_ids:
        url = f"{base_url}/?user={user_id}"
        user_url_list.append({'User_id': user_id, 'url': url})
    
    # 儲存成 CSV
    df_url = pd.DataFrame(user_url_list)
    df_url.to_csv('user_dashboard_urls.csv', index=False)
    return df_url

def calc_longest_streak(days):
    """計算最長連續天數"""
    if not days:
        return 0
    days = sorted(set(days))
    max_streak = streak = 1
    for i in range(1, len(days)):
        if days[i] == days[i-1] + 1:
            streak += 1
        else:
            streak = 1
        max_streak = max(max_streak, streak)
    return max_streak

def get_user_stats(df_apr):
    """計算每位用戶的統計資料"""
    user_stats = []
    for user_id, group in df_apr.groupby('User_id'):
        day_list = sorted(group['Day'].unique())
        total_days = len(day_list)
        longest_streak = calc_longest_streak(day_list)
        user_stats.append({
            'User_id': user_id,
            '總參與天數': total_days,
            '連續參與天數': longest_streak
        })
    
    user_stats_df = pd.DataFrame(user_stats)
    user_stats_df = user_stats_df.sort_values(['連續參與天數', '總參與天數'], ascending=[False, False])
    user_stats_df['排名'] = range(1, len(user_stats_df)+1)
    return user_stats_df

def log_user_visit(user_id):
    """記錄用戶瀏覽紀錄"""
    os.makedirs('dashboard', exist_ok=True)
    visit_log_path = 'dashboard/user_visit_log.csv'
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    if 'last_user' not in st.session_state or st.session_state.last_user != user_id:
        log_df = pd.DataFrame([[user_id, now]], columns=['User_id', 'Timestamp'])
        if os.path.exists(visit_log_path):
            log_df.to_csv(visit_log_path, mode='a', header=False, index=False)
        else:
            log_df.to_csv(visit_log_path, mode='w', header=True, index=False)
        st.session_state.last_user = user_id

def main():
    # 載入資料
    df_apr = load_data()
    user_ids = df_apr['User_id'].unique()
    
    # 產生使用者網址列表
    generate_user_urls()

    # UI - 使用者下拉選單
    selected_user = st.sidebar.selectbox("請選擇使用者", user_ids)

    
    # 獲取網址參數中的使用者ID (已在頁面配置時獲取)
    if selected_user is None or selected_user == 'User':
        st.error("請提供有效的使用者ID參數，例如: ?user=your_user_id")
        st.write("**可用的使用者ID:**")
        for user_id in user_ids:
            st.write(f"- {user_id}")
        st.stop()
    
    if selected_user not in user_ids:
        st.error(f"使用者ID '{selected_user}' 不存在於資料中")
        st.write("**可用的使用者ID:**")
        for user_id in user_ids:
            st.write(f"- {user_id}")
        st.stop()
    
    # 記錄瀏覽紀錄
    log_user_visit(selected_user)
    
    # 計算統計資料
    user_stats_df = get_user_stats(df_apr)
    honor_board = user_stats_df.head(10)
    
    # CSS 樣式
    st.markdown("""
        <style>
        body, .stApp {
            background-color: #ffffff !important;
        }
        .main-title {font-size:3rem;color:#000000;font-weight:bold;text-align:center;margin-bottom:1.5rem;}
        .sub-title {font-size:1.3rem;color:#000000;font-weight:bold;margin-top:1.5rem;margin-bottom:0.5rem;}
        </style>
    """, unsafe_allow_html=True)
    
    # 主標題
    st.markdown(f'<div class="main-title">{selected_user}的{year}年{month}月每日一題儀表板</div>', unsafe_allow_html=True)
    
    # 主要內容區域
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # ===== 登入日曆 =====
        st.markdown('<div class="sub-title">登入日曆</div>', unsafe_allow_html=True)
        user_days = df_apr[df_apr['User_id'] == selected_user]['Day'].unique().tolist()
        cal = calendar.monthcalendar(year, month)
        
        fig, ax = plt.subplots(figsize=(4.5, 4))
        ax.axis('off')
        ax.text(0.5, 0.82, f'{year}年{month}月',
            transform=ax.transAxes,
            ha='center', va='center',
            fontsize=17, fontweight='bold',
            color='#333333', fontproperties=font)
        
        cell_size = 0.5
        start_x = 0.2
        start_y = len(cal) * cell_size
        
        # 星期標題
        weekdays = ['一', '二', '三', '四', '五', '六', '日']
        for i, wd in enumerate(weekdays):
            ax.text(start_x + i * cell_size + cell_size / 2, start_y + 0.15,
                    wd, ha='center', va='center', fontsize=12, color='#333333', fontproperties=font)
        
        # 畫出每一天
        for row_idx, week in enumerate(cal):
            for col_idx, day in enumerate(week):
                if day == 0:
                    continue
                x = start_x + col_idx * cell_size
                y = start_y - (row_idx + 1) * cell_size
                is_login = day in user_days
                color = '#b7e4c7' if is_login else '#f8f9fa'
                ax.add_patch(plt.Rectangle((x, y), cell_size, cell_size,
                                           color=color, ec='#a5a5a5', lw=1.2))
                ax.text(x + cell_size / 2, y + cell_size / 2, str(day),
                        ha='center', va='center', fontsize=12, color='#222', fontproperties=font)
        
        ax.set_xlim(0, start_x + 7 * cell_size + 0.5)
        ax.set_ylim(0, start_y + 1)
        plt.tight_layout(rect=[0, 0, 1, 1])
        st.pyplot(fig)
        
        # ===== 榮譽榜 =====
        st.markdown('<div class="sub-title">榮譽榜</div>', unsafe_allow_html=True)
        honor_show = honor_board[['排名', 'User_id', '連續參與天數', '總參與天數']].reset_index(drop=True)
        st.dataframe(honor_show, use_container_width=True, hide_index=True)
    
    with col2:
        st.markdown("<div style='height:70px;'></div>", unsafe_allow_html=True)
        
        # ===== 四個正方形字卡 =====
        card_titles = ['參與率', '連續天數', '擅長領域', '不擅長領域']
        card_values = [
            f"{np.random.randint(60, 100)}%",
            f"{np.random.randint(3, 15)} 天🔥",
            np.random.choice(['Python', 'EDA', '商業分析', '數據分析']),
            np.random.choice(['Python', 'EDA', '商業分析', '數據分析'])
        ]
        card_colors = ['#97b3ae', '#d2e0d3', '#f0ddd6', '#f2c3d9']
        
        card_cols = st.columns(4, gap='small')
        for i in range(4):
            with card_cols[i]:
                st.markdown(
                    f"""
                    <div style='
                        background-color:{card_colors[i]};
                        color:black;
                        border-radius:16px;
                        width:220px;
                        height:220px;
                        display:flex;
                        flex-direction:column;
                        align-items:center;
                        justify-content:center;
                        margin-bottom:10px;
                        box-shadow:0 2px 8px #e0e0e0;
                    '>
                        <div style='font-size:1.1rem;font-weight:bold;margin-bottom:6px;'>{card_titles[i]}</div>
                        <div style='font-size:1.7rem;font-weight:bold;'>{card_values[i]}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        
        # ===== 堆疊長條圖 =====
        st.markdown('<div class="sub-title">各類表現</div>', unsafe_allow_html=True)
        
        bar_cols = st.columns(2, gap='large')
        
        with bar_cols[0]:
            categories1 = ['EDA', 'ML', 'Preprocessing']
            correct1 = np.random.randint(5, 11, size=3)
            wrong1 = np.random.randint(2, 6, size=3)
            bar_width = 0.6
            x1 = np.arange(len(categories1))
            
            fig1, ax1 = plt.subplots(figsize=(4, 4))
            ax1.bar(x1, correct1, bar_width, label='Correct', color='#6ec6ff', edgecolor='none')
            ax1.bar(x1, wrong1, bar_width, bottom=correct1, label='Wrong', color='#f7c97f', edgecolor='none')
            ax1.set_xticks(x1)
            ax1.set_xticklabels(categories1, fontsize=13, fontproperties=font)
            ax1.set_yticks(np.arange(0, max(correct1+wrong1)+2, 2))
            ax1.legend(loc='upper center', ncol=2, bbox_to_anchor=(0.5, 1.08), fontsize=13)
            ax1.spines['top'].set_visible(False)
            ax1.spines['right'].set_visible(False)
            ax1.spines['left'].set_visible(False)
            ax1.spines['bottom'].set_color('#cccccc')
            ax1.tick_params(axis='y', length=0)
            ax1.tick_params(axis='x', length=0)
            plt.tight_layout(pad=0.5)
            st.pyplot(fig1)
        
        with bar_cols[1]:
            categories2 = ['Python', 'SQL', '統計']
            correct2 = np.random.randint(3, 10, size=3)
            wrong2 = np.random.randint(1, 7, size=3)
            x2 = np.arange(len(categories2))
            
            fig2, ax2 = plt.subplots(figsize=(4, 4))
            ax2.bar(x2, correct2, bar_width, label='Correct', color='#6ec6ff', edgecolor='none')
            ax2.bar(x2, wrong2, bar_width, bottom=correct2, label='Wrong', color='#f7c97f', edgecolor='none')
            ax2.set_xticks(x2)
            ax2.set_xticklabels(categories2, fontsize=13, fontproperties=font)
            ax2.set_yticks(np.arange(0, max(correct2+wrong2)+2, 2))
            ax2.legend(loc='upper center', ncol=2, bbox_to_anchor=(0.5, 1.08), fontsize=13)
            ax2.spines['top'].set_visible(False)
            ax2.spines['right'].set_visible(False)
            ax2.spines['left'].set_visible(False)
            ax2.spines['bottom'].set_color('#cccccc')
            ax2.tick_params(axis='y', length=0)
            ax2.tick_params(axis='x', length=0)
            plt.tight_layout(pad=0.5)
            st.pyplot(fig2)

if __name__ == "__main__":
    main()