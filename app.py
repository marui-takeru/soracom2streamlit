# 以下を「app.py」に書き込み

import pandas as pd
import json
import requests
import datetime
import streamlit as st

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
st.title('堂野窪地区　傾斜センサ')

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
selected_week = st.selectbox('閲覧したい週を選んでください', ['今週', '先週', '2週間前'])

# Calculate the time range based on the selected option
current_time = datetime.datetime.now()

if selected_week == '今週':
    date_start = current_time - datetime.timedelta(days=current_time.weekday())
elif selected_week == '先週':
    date_start = current_time - datetime.timedelta(days=current_time.weekday() + 7)
elif selected_week == '2週間前':
    date_start = current_time - datetime.timedelta(days=current_time.weekday() + 14)

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
urls = [eval(f"url{i:02d}") for i in range(1, 11)]

# Select a URL using a dropdown
selected_index = st.selectbox('閲覧したい傾斜センサを選んでください', range(1, 11))
selected_url = urls[selected_index - 1]

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

    df = pd.DataFrame(inclination, columns=['日付', '傾斜角X', '傾斜角Y', '傾斜角Z', '電圧', '気温', '湿度'])

    # Convert columns to appropriate data types
    df['日付'] = pd.to_datetime(df['日付'], errors='coerce')
    df['傾斜角X'] = pd.to_numeric(df['傾斜角X'], errors='coerce')
    df['傾斜角Y'] = pd.to_numeric(df['傾斜角Y'], errors='coerce')
    df['傾斜角Z'] = pd.to_numeric(df['傾斜角Z'], errors='coerce')
    df['電圧'] = pd.to_numeric(df['電圧'], errors='coerce')
    df['気温'] = pd.to_numeric(df['気温'], errors='coerce')
    df['湿度'] = pd.to_numeric(df['湿度'], errors='coerce')


    # Display the DataFrame
    st.write(df)
    
    # Allow users to select the y-axis data
    selected_y_axes = ['傾斜角X', '傾斜角Y', '電圧', '気温', '湿度']
    axis_labels = {'傾斜角X': 'Angle_X', '傾斜角Y': 'Angle_Y', '電圧': 'Voltage', '気温': 'Temperature', '湿度': 'Humidity'}
    
    # Create subplots for each selected y-axis
    for selected_y_axis in selected_y_axes:
        st.write(selected_y_axis)
        st.scatter_chart(df.set_index('日付')[selected_y_axis])  # Use set_index to use '日付' as index
    
    # Display error message if data fetching failed
if response.status_code != 200:
    st.error(f"Failed to fetch data from {selected_url}. Status code: {response.status_code}")
