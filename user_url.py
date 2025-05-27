# -*- coding: utf-8 -*-

import pandas as pd

def generate_user_dashboard_urls():
    """
    讀取 data.csv 並產生每位使用者的專屬儀表板網址
    儲存至 user_dashboard_urls.csv
    """
    # 讀取資料
    try:
        df = pd.read_csv('data.csv')
        print(f"成功讀取 data.csv，共 {len(df)} 筆資料")
    except FileNotFoundError:
        print("錯誤：找不到 data.csv 檔案")
        return
    
    # 取得所有 unique user id
    user_ids = df['User_id'].unique().tolist()
    print(f"發現 {len(user_ids)} 個不同的使用者ID")
    
    # 設定基礎網址 (請根據你的實際部署網址修改)
    base_url = "http://localhost:8501"  # 本地測試
    # base_url = "https://your-streamlit-app.herokuapp.com"  # 正式部署時使用
    
    # 產生每位 user 的專屬網址
    user_url_list = []
    for user_id in user_ids:
        url = f"{base_url}/?user={user_id}"
        user_url_list.append({
            'User_id': user_id, 
            'url': url
        })
        print(f"使用者 {user_id}: {url}")
    
    # 存成 csv
    df_url = pd.DataFrame(user_url_list)
    df_url.to_csv('user_dashboard_urls.csv', index=False)
    print(f"\n成功產生 user_dashboard_urls.csv，包含 {len(user_url_list)} 個使用者網址")
    
    return df_url

if __name__ == "__main__":
    generate_user_dashboard_urls()
