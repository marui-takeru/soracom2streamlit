import streamlit as st
import pandas as pd
import boto3
import json
import datetime
from sklearn.linear_model import LinearRegression
from botocore.exceptions import ClientError

# Streamlit app
st.title('堂野窪 傾斜センサ')

# DynamoDBのクライアントを初期化
# Streamlit Secretsを使用して認証情報を安全に管理
try:
    # ローカル実行の場合、boto3はデフォルトの認証情報（~/.aws/credentials）を使用します。
    # Streamlit Cloudの場合、secrets.tomlで設定します。
    dynamodb = boto3.resource('dynamodb',
        region_name=st.secrets.aws.region_name,
        aws_access_key_id=st.secrets.aws.aws_access_key_id,
        aws_secret_access_key=st.secrets.aws.aws_secret_access_key
    )
    table_name = st.secrets.aws.dynamodb_table_name
    table = dynamodb.Table(table_name)
except ClientError as e:
    st.error(f"AWS認証エラー: {e}")
    st.stop()

# センサー名を定義
# Lambda関数と同じリストを使用
url_display_names = {
    "１：上田宅上": "url01",
    "２：井上宅上": "url02",
    "３：名古谷1": "url03",
    "４：久保田宅上": "url04",
    "５：泉谷": "url05",
    "６：清水宅上": "url06",
    "７：名古谷2": "url07",
    "８：横之地": "url08",
    "９：集会所上": "url09",
    "１０：ヒラノジ": "url10"
}
sensor_ids = list(url_display_names.keys())

# 最新のデータ取得時刻と角度変化を格納する辞書
latest_data_summary = {}

# データ取得期間の設定（7日間）
current_time_ms = int(datetime.datetime.now().timestamp() * 1000)
one_week_ago_ms = current_time_ms - 7 * 24 * 60 * 60 * 1000

# 各センサーごとにデータを取得し、加工・表示
for sensor_id in sensor_ids:
    st.subheader(sensor_id)
    
    # DynamoDBからデータを取得
    try:
        response = table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key('sensorId').eq(sensor_id),
            FilterExpression=boto3.dynamodb.conditions.Attr('timestamp').between(one_week_ago_ms, current_time_ms)
        )
        items = response['Items']
    except ClientError as e:
        st.error(f"DynamoDBデータの読み込みエラー（{sensor_id}）：{e}")
        continue
    
    if not items:
        st.warning(f'{sensor_id}のデータが存在しません。')
        latest_data_summary[sensor_id] = {'latest_date': 'N/A', 'latest_diff_x': 'N/A'}
        continue

    # データをPandas DataFrameに変換
    df = pd.DataFrame(items)
    df['日付'] = pd.to_datetime(df['timestamp'], unit='ms')
    
    # NaNを含む行を削除
    df = df.dropna()
    
    # データが存在するかチェック
    if not df.empty:
        # データを時系列順にソート
        df = df.sort_values('日付', ascending=False)
        
        # 平均気温の計算
        Tave = df['temperature'].mean()

        # 選択した期間内のデータを使用して単回帰分析を行う
        X = df['temperature'].values.reshape(-1, 1)
        y = df['inclination_x'].values
        
        # 線形回帰モデルを構築
        reg = LinearRegression().fit(X, y)

        # 回帰係数を取得
        reg_coef = reg.coef_[0]

        # データの修正
        df['補正角度'] = df['inclination_x'] - reg_coef * (df['temperature'] - Tave)

        # 前回の値との差分を計算して新しい列を追加
        df['角度変化'] = -df['補正角度'].diff().shift(-1)
        df['角度変化'].iloc[-1] = 0

        # 最新のデータ取得時刻を表示
        latest_date = df['日付'].max()

        # '角度変化'の最新値を取得
        latest_diff_x = df['角度変化'].iloc[0] if not df.empty else 'N/A'
        
        # 背景色の設定
        background_color = '#ffffff'  # Default white
        if 0.0 <= abs(latest_diff_x) < 0.05:
            background_color = '#ccffcc'  # Green
        elif 0.05 <= abs(latest_diff_x) < 0.1:
            background_color = '#ffff99'  # Yellow
        else:
            background_color = '#ff9999'  # Red
            
        # 最新データが1時間以上前のものであれば背景色をグレーに設定
        if latest_date is not pd.NaT and (datetime.datetime.now() - latest_date) > datetime.timedelta(hours=1):
            background_color = '#d3d3d3'  # Gray

        # Display the latest values with background color
        st.markdown(
            f"""
            <div style="background-color: {background_color}; padding: 10px; border-radius: 5px;">
                <p><strong>最新のデータ取得時刻：</strong>{latest_date}</p>
                <p><strong>最新の角度変化：</strong>{latest_diff_x}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

# 詳細は別アプリへ移動するリンク
st.markdown(
    """
    詳細は[こちら](https://soracom2app-devapp2.streamlit.app/)をクリックしてください。
    """,
    unsafe_allow_html=True
)
