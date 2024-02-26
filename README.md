# SORACOM Harvest Dataでデータを蓄積する（グループの設定）

1. [SORACOMユーザーコンソール](https://auth.soracom.io/login/?redirect=https%3A%2F%2Fconsole.soracom.io%2Fdashboard)にログインした後[Menu]>[SIM管理]とクリックしてSIM管理画面を開く．  
2. SORACOM HarvestDataでデータの収集を行いたいSIM（WioLTEに取り付けたSIM）にチェックを付け，[操作]>[所属グループ変更]とクリックする．
3. 「新しい所属グループ」のプルダウンボックスをクリックした後，[新しいグループを作成...]をクリック．
4. 「グループ作成」のグループ名を入力して[グループ作成]をクリック．
5. 新しい所属グループが先ほど作成したグループになっていることを確認したら[グループ変更]をクリック．
6. 自動的にSIM管理画面に戻る．SIMの「グループ」に先ほど作ったグループが設定されていることを確認．

# SORACOM Harvest Dataでデータを蓄積する（グループの設定）

1. SIM管理画面から，WioLTEに割り当てたグループ名をクリック．
2. [SORACOM Air for Cellular設定]をクリックして設定ができるように開く．
3. [SORACOM Air for Cellular設定]でメタデータサービス設定（スイッチ）をONに設定する．
4. [SORACOM Harvest Data設定]をクリックして設定ができるように開く．
5. 「SORACOM Harvest Data設定」で（スイッチ）をONに設定する．

# SORACOM Harvest Dataでデータを蓄積する（メタデータの設定）

1. SORACOMユーザーコンソールの[Menu]>[SIM管理]とクリックしてSIM管理画面を開く．
2. メタデータを設定したいSIM（WioLTEに取り付けたSIM）にチェックを付け，[詳細]をクリックする．
3. 「SIM詳細」で[タグ]>「＋」をクリック
4. 「タグの編集」で名前（Key）と値（Value）を設定する．  
設定例）  
名前：config_json  
値　：{"TV_OFF_THRESHOLD": 4, "TV_ON_DARK_THRESHOLD": 30, "TV_ON_BRIGHT_THRESHOLD": 200, "SENSING_INTERVAL_MS": 1000, "SAMPLING_COUNT": 10}
5. [保存]をクリックする．
