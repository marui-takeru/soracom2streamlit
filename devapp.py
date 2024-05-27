import pandas as pd
import json
import requests
import datetime
import streamlit as st
import base64
from sklearn import linear_model
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt

# APIの認証情報を環境変数から取得
# Streamlit community cloudの「secrets」からSoracomAPIを取得
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
st.title('【試行段階】　堂野窪傾斜計')

#apiキーとトークンを作成
auth = (api_username, api_password)
headers = {'Content-Type': 'application/json'}
data = {'email': api_email, 'password': api_data_password}

response = requests.post(api_post, auth=auth, headers=headers, data=json.dumps(data))
response.raise_for_status()
auth_response = response.json()

api_key = auth_response['apiKey']
api_token = auth_response['token']

# Allow users to select the time range
selected_week = st.selectbox('閲覧したい週を選んでください', ['今週', '先週', '2週間前', '3週間前'])

# Calculate the time range based on the selected option
current_time = datetime.datetime.now()

if selected_week == '今週':
    date_start = current_time - datetime.timedelta(days=current_time.weekday())
elif selected_week == '先週':
    date_start = current_time - datetime.timedelta(days=current_time.weekday() + 7)
elif selected_week == '2週間前':
    date_start = current_time - datetime.timedelta(days=current_time.weekday() + 14)
elif selected_week == '3週間前':
    date_start = current_time - datetime.timedelta(days=current_time.weekday() + 21)

# Set the start and end date times
date_start = date_start.replace(hour=0, minute=0, second=0, microsecond=0)
date_end = date_start + datetime.timedelta(days=7)

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

# Select a URL using a dropdown
selected_display_name = st.selectbox('閲覧したい傾斜センサを選んでください', list(url_display_names.keys()))
selected_url = url_display_names[selected_display_name]

# Fetch data for the selected URL
response = requests.get(selected_url, headers=headers, params=params)

if response.status_code == 200:
    data = response.json()

    # Create DataFrame
    inclination = []
    for i in range(len(data)):
        inclination.append(data[i]['content'])

    for i in range(len(inclination)):
        tmp = inclination[i].split(sep=',')
        inclination[i] = tmp

    # 前回の値を保持するための変数
    prev_value = None
    
    def convert_to_numeric_with_threshold(value):
        global prev_value
        # 前回の値が存在しない場合はそのまま数値に変換
        if prev_value is None:
            prev_value = value
            return pd.to_numeric(value, errors='coerce')
    
        # 前回の値との差が3度以上の場合はNaNを返す
        if abs(float(value) - float(prev_value)) >= 3:
            return float('NaN')
    
        # 差が3度未満の場合はそのまま数値に変換
        prev_value = value
        return pd.to_numeric(value, errors='coerce')

    df = pd.DataFrame(inclination, columns=['日付', '傾斜角X', '傾斜角Y', '傾斜角Z', '電圧', '気温', '湿度'])

    # Convert columns to appropriate data types
    df['日付'] = pd.to_datetime(df['日付'], errors='coerce')
    df['傾斜角X（縦方向）'] = df['傾斜角X'].apply(convert_to_numeric_with_threshold)
    df['傾斜角Y（横方向）'] = pd.to_numeric(df['傾斜角Y'], errors='coerce')
    df['傾斜角Z'] = pd.to_numeric(df['傾斜角Z'], errors='coerce')
    df['電圧'] = pd.to_numeric(df['電圧'], errors='coerce')
    df['気温'] = pd.to_numeric(df['気温'], errors='coerce')
    df['湿度'] = pd.to_numeric(df['湿度'], errors='coerce')

    # データ数の表示
    num_samples = len(df)
    st.write(f'使用されたデータ数: {num_samples}')

    # 平均気温の計算
    Tave = df['気温'].mean()

    # 選択した期間内のデータを使用して単回帰分析を行う
    X = df['気温'].values.reshape(-1, 1)
    y = df['傾斜角X（縦方向）'].values
    
    # 線形回帰モデルを構築
    reg = LinearRegression().fit(X, y)
    
    # 回帰係数を取得
    reg_coef = reg.coef_[0]
    st.write(f'回帰係数:{reg_coef}')

    # データの修正
    df['Predicted_X'] = df['傾斜角X（縦方向）'] - reg_coef * (df['気温'] - Tave)
    df['Predicted_Y'] = df['傾斜角Y（横方向）'] - reg_coef * (df['気温'] - Tave)

    st.write(f'平均気温{Tave}')
    
    # グラフのプロット
    fig, ax = plt.subplots(3, 1, figsize=(10, 16))
    
    ax[0].plot(df['日付'], df['Predicted_X'], label='Corrected X', linestyle='--')
    ax[0].plot(df['日付'], df['傾斜角X（縦方向）'], label='Original X')
    ax[0].set_title('X')
    ax[0].legend()

    ax[1].plot(df['日付'], df['傾斜角Y（横方向）'], label='Corrected Y', linestyle='--')
    ax[1].plot(df['日付'], df['Predicted_Y'], label='Corrected Y')
    ax[1].set_title('Y')
    ax[1].legend()

    ax[2].plot(df['日付'], df['気温'], label='Temperature')
    ax[2].plot(df['日付'], df['気温'], label='Temperature')
    ax[2].set_title('Temperature')
    ax[2].legend()

    st.pyplot(fig)
    
    # Display error message if data fetching failed
if response.status_code != 200:
    st.error(f"Failed to fetch data from {selected_url}. Status code: {response.status_code}")
