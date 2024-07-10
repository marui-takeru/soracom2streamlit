import streamlit as st
import pandas as pd
import json
import requests
import datetime
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt

# APIの認証情報を環境変数から取得
api_username = st.secrets.APIs.api_username
api_password = st.secrets.APIs.api_password
api_email = st.secrets.APIs.api_email
api_data_password = st.secrets.APIs.api_data_password
api_post = st.secrets.APIs.api_post
url01 = st.secrets.APIs.url01
url02 = st.secrets.APIs.url02
url03 = st.secrets.APIs.url03
url04 = st.secrets.APIs.url04
url05 = st.secrets.APIs.url05
url06 = st.secrets.APIs.url06
url07 = st.secrets.APIs.url07
url08 = st.secrets.APIs.url08
url09 = st.secrets.APIs.url09
url10 = st.secrets.APIs.url10

# Streamlit app
st.title('【開発版2】堂野窪 傾斜センサ')

# APIキーとトークンを作成
auth = (api_username, api_password)
headers = {'Content-Type': 'application/json'}
data = {'email': api_email, 'password': api_data_password}

response = requests.post(api_post, auth=auth, headers=headers, data=json.dumps(data))
response.raise_for_status()
auth_response = response.json()

api_key = auth_response['apiKey']
api_token = auth_response['token']

# Calculate the time range based on the selected option
current_time = datetime.datetime.now()

date_end = current_time  # 現在の日付
date_start = current_time - datetime.timedelta(days=7)  # 7日前の日付

# Set the start and end date times
date_start = date_start.replace(hour=0, minute=0, second=0, microsecond=0)
date_end = date_end.replace(hour=23, minute=59, second=59, microsecond=999999)

# Convert to Unix timestamps
unix_timestamp_ms_start = int(date_start.timestamp() * 1000)
unix_timestamp_ms_end = int(date_end.timestamp() * 1000)

headers = {
    "Content-Type": "application/json",
    "X-Soracom-API-Key": api_key,
    "X-Soracom-Token": api_token
}

params = {
    "limit": 100000, #取得できる最大のデータ数
    'from': unix_timestamp_ms_start,
    'to': unix_timestamp_ms_end
}

# Define URLs
url_display_names = {
    "１：上田宅上": url01,
    "２：井上宅上": url02,
    "３：名古谷1": url03,
    "４：久保田宅上": url04,
    "５：泉谷": url05,
    "６：清水宅上": url06,
    "７：名古谷2": url07,
    "８：横之地": url08,
    "９：集会所上": url09,
    "１０：ヒラノジ": url10
}

# Fetch data for all URLs
all_data = []

for display_name, url in url_display_names.items():
    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        data = response.json()
        for item in data:
            inclination = item['content'].split(',')
            inclination.append(display_name)
            all_data.append(inclination)
    else:
        st.error(f"Failed to fetch data from {url}. Status code: {response.status_code}")

# Create DataFrame
if all_data:
    df = pd.DataFrame(all_data, columns=['日付', '傾斜角X', '傾斜角Y', '傾斜角Z', '電圧', '気温', '湿度', 'センサー'])

    # Convert columns to appropriate data types
    df['日付'] = pd.to_datetime(df['日付'], errors='coerce')
    df['傾斜角X（縦方向）'] = df['傾斜角X'].apply(pd.to_numeric, errors='coerce')
    df['気温'] = pd.to_numeric(df['気温'], errors='coerce')
    
    # NaNを含む行を削除する
    df = df.dropna()

    # データが存在するかチェック
    if not df.empty:
        # 平均気温の計算
        Tave = df['気温'].mean()
    
        # 選択した期間内のデータを使用して単回帰分析を行う
        X = df['気温'].values.reshape(-1, 1)
        y = df['傾斜角X（縦方向）'].values
        
        # 線形回帰モデルを構築
        reg = LinearRegression().fit(X, y)
        
        # 回帰係数を取得
        reg_coef = reg.coef_[0]
    
        # データの修正
        df['補正角度'] = df['傾斜角X（縦方向）'] - reg_coef * (df['気温'] - Tave)
    
        # 前回の値との差分を計算して新しい列を追加
        df['角度変化'] = -df['補正角度'].diff().shift(-1)
        df['角度変化'].iloc[-1] = 0  # 最後の行に0を設定
    
        # Display data for each sensor
        for sensor in url_display_names.keys():
            st.subheader(sensor)
            sensor_df = df[df['センサー'] == sensor]

            # 最新のデータ取得時刻を表示
            latest_date = sensor_df['日付'].max()
            st.write(f'最新のデータ取得時刻：{latest_date}')
            
            # '角度変化'の最新値を取得
            st.write(f'最新の角度変化：{latest_diff_x}')
            
    else:
        st.error('データが存在しません。')
else:
    st.error('データが取得できませんでした。')

