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
url11 = st.secrets.APIs.url11
url12 = st.secrets.APIs.url12

# Streamlit app
st.title('【開発版】　堂野窪傾斜計')

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
date_start = current_time - datetime.timedelta(days=7)  # 過去7日分のデータを描画

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
    "１０：ヒラノジ": url10,
    "１１：予備１": url11,
    "１２：予備２": url12
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
    for item in data:
        inclination.append(item['content'].split(','))

    # 前回の値を保持するための変数
    prev_value = None
    
    # 数値型に変換し、閾値条件を適用する関数
    def convert_to_numeric_with_threshold(value):
        global prev_value
        try:
            current_value = float(value)
            if prev_value is None:
                prev_value = current_value
                return current_value
    
            # 前回の値との差が3度以上の場合はNaNを返す
            if abs(current_value - prev_value) >= 3:
                return float('NaN')
    
            # 差が3度未満の場合はそのまま数値に変換
            prev_value = current_value
            return current_value
        except ValueError:
            return float('NaN')

    df = pd.DataFrame(inclination, columns=['日付', '傾斜角X', '傾斜角Y', '傾斜角Z', '電圧', '気温', '湿度'])

    # Convert columns to appropriate data types
    df['日付'] = pd.to_datetime(df['日付'], errors='coerce')
    df['傾斜角X（縦方向）'] = df['傾斜角X'].apply(convert_to_numeric_with_threshold)
    df['傾斜角Y（横方向）'] = pd.to_numeric(df['傾斜角Y'])
    df['傾斜角Z'] = pd.to_numeric(df['傾斜角Z'], errors='coerce')
    df['電圧'] = pd.to_numeric(df['電圧'], errors='coerce')
    df['気温'] = pd.to_numeric(df['気温'], errors='coerce')
    df['湿度'] = pd.to_numeric(df['湿度'], errors='coerce')
    # NaNを含む行を削除する
    df = df.dropna()

    # データが存在するかチェック
    if not df.empty:
        # 最新のデータ取得時刻を表示
        latest_date = df['日付'].max()
        st.write(f'最新のデータ取得時刻：{latest_date}')
        
        # データ数の表示
        num_samples = len(df)
        st.write(f'使用されたデータ数：{num_samples}個')
        
        # 平均気温の計算
        Tave = df['気温'].mean()

        # 選択した期間内のデータを使用して単回帰分析を行う
        X = df['気温'].values.reshape(-1, 1)
        y = df['傾斜角X（縦方向）'].values
        
        # 線形回帰モデルを構築
        reg = LinearRegression().fit(X, y)
        
        # 回帰係数を取得
        reg_coef = reg.coef_[0]
        st.write(f'回帰係数：{reg_coef}')

        # データの修正
        df['補正角度'] = df['傾斜角X（縦方向）'] - reg_coef * (df['気温'] - Tave)
        st.write(f'平均気温：{Tave}℃')

        # 前回の値との差分を計算して新しい列を追加
        df['角度変化'] = -df['補正角度'].diff().shift(-1)
        df['角度変化'].iloc[-1] = 0  # 最後の行に0を設定
    
        #  '角度変化'の最新値を取得
        latest_diff_x = df['角度変化'].iloc[0]
        st.write(f'最新の差分値：{latest_diff_x}')

        # 背景色の設定
        background_color = '#ffffff'  # Default white
        if 0.0 <= abs(latest_diff_x) < 0.05:
            background_color = '#ccffcc'  # Green
        elif 0.05 <= abs(latest_diff_x) < 0.1:
            background_color = '#ffff99'  # Yellow
        else :
            background_color = '#ff9999'  # Red

        background_color_css = f"""
        <style>
            .stApp {{
                background-color: {background_color};
            }}
        </style>
        """
        st.markdown(background_color_css, unsafe_allow_html=True)

        # 累積変化の計算
        df['Cumulative_Diff_X'] = df['角度変化'].cumsum()
        
        # グラフのプロット
        fig, ax = plt.subplots(5, 1, figsize=(10, 20))
        
        ax[0].plot(df['日付'], df['補正角度'], label='Corrected X', linestyle='--')
        ax[0].plot(df['日付'], df['傾斜角X（縦方向）'], label='Original X')
        ax[0].set_title('Value X')
        ax[0].legend()

        ax[1].plot(df['日付'], df['角度変化'], label='Diff X', color='red')
        ax[1].set_title('Difference X')
        ax[1].legend()
        # 縦軸のレンジを -0.2 から 0.2 までで固定
        ax[1].set_ylim(-0.2, 0.2)
        # 縦軸の値が0.05と0.1の場所に波線を描画
        ax[1].axhline(y=0.05, color='black', linestyle='dotted', label='注意')
        ax[1].axhline(y=-0.05, color='black', linestyle='dotted', label='注意')
        ax[1].axhline(y=0.1, color='red', linestyle='dotted', label='危険')
        ax[1].axhline(y=-0.1, color='red', linestyle='dotted', label='危険')
        
        ax[2].plot(df['日付'], df['Cumulative_Diff_X'], label='Cumulative Diff X', color='green')
        ax[2].set_title('Cumulative Difference X')
        ax[2].legend()

        ax[3].plot(df['日付'], df['気温'], label='Temperature')
        ax[3].set_title('Temperature')
        ax[3].legend()
        
        ax[4].plot(df['日付'], df['電圧'], label='Volt')
        ax[4].set_title('Volt')
        ax[4].legend()

        st.pyplot(fig)

        # 表の作成
        # 表示したい列の順番を指定
        columns_order = ['角度変化', '補正角度', '傾斜角X', '電圧', '気温', '湿度']
        
        # 表の作成
        st.write(df.set_index('日付')[columns_order])
            
    else:
        st.error('過去7日分のデータが存在しません。')
else:
    st.error(f"Failed to fetch data from {selected_url}. Status code: {response.status_code}")
