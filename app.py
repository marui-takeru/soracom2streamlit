import streamlit as st
import pandas as pd
import json
import requests
import datetime
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt
import streamlit.components.v1 as components

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
st.title('堂野窪　傾斜センサ')

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
date_start = current_time - datetime.timedelta(days=7)  # 今週の月曜日の日付

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
    "３：名古谷1": url03,
    "５：泉谷": url05
}
# グラフを描画するための空のリストを用意
fig, axs = plt.subplots(len(urls), 1, figsize=(12, 10), sharex=True, squeeze=False)

for i, (display_name, url) in enumerate(urls.items()):
    # Fetch data for the selected URL
    response = requests.get(url, headers=headers, params=params)

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
        df['傾斜角Y（横方向）'] = df['傾斜角Y'].apply(convert_to_numeric_with_threshold)
        df['傾斜角Z'] = pd.to_numeric(df['傾斜角Z'], errors='coerce')
        df['電圧'] = pd.to_numeric(df['電圧'], errors='coerce')
        df['気温'] = pd.to_numeric(df['気温'], errors='coerce')
        df['湿度'] = pd.to_numeric(df['湿度'], errors='coerce')
        # NaNを含む行を削除する
        df = df.dropna()

        # データ数の表示
        num_samples = len(df)
        st.write(f"センサー「{display_name}」のデータ数: {num_samples} サンプル")

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
        df['Predicted_X'] = df['傾斜角X（縦方向）'] - reg_coef * (df['気温'] - Tave)

        # 前回の値との差分を計算して新しい列を追加
        df['Diff_X'] = df['Predicted_X'].diff()

        # Diff_Xの最新値を取得
        latest_diff_x = df['Diff_X'].iloc[-1]

        # 背景色の設定
        if 0 <= abs(latest_diff_x) < 0.01:
            background_color = '#ccffcc'  # Green
        elif 0.01 <= abs(latest_diff_x) < 0.05:
            background_color = '#ffff99'  # Yellow
        elif 0.05 <= abs(latest_diff_x) < 0.1:
            background_color = '#ff9999'  # Red
        else:
            background_color = '#ffffff'  # Default white

        # 累積変化の計算
        df['Cumulative_Diff_X'] = df['Diff_X'].cumsum()

        # グラフのプロット
        ax = axs[i, 0]
        ax.set_facecolor(background_color)
        ax.plot(df['日付'], df['Diff_X'], label='Diff_X', color='black')
        ax.set_title(f'{display_name} の傾斜角Xの変化')
        ax.set_xlabel('日付')
        ax.set_ylabel('傾斜角Xの変化')
        ax.legend()
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
        ax.xaxis.set_major_locator(mdates.DayLocator())
        ax.tick_params(axis='x', rotation=45)

        # 縦軸のレンジを -0.2 から 0.2 までで固定
        ax.set_ylim(-0.2, 0.2)

# 全体のレイアウト調整
plt.tight_layout()

# Streamlit でグラフを表示
st.pyplot(fig)
