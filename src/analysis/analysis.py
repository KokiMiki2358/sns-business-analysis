import os
import pandas as pd
from dotenv import load_dotenv
from apify_client import ApifyClient

# 分析対象プロファイルと出力ファイルの設定
TARGET_PROFILES = ["nba"] 
RESULT_FILE = "tiktok_metrics_report.csv"

def analyze_tiktok():
    load_dotenv()
    client = ApifyClient(os.getenv("APIFY_TOKEN"))

    all_data = []

    print(f"[INFO] 抽出開始 (対象: {len(TARGET_PROFILES)}件)")

    for profile in TARGET_PROFILES:
        try:
            print(f"[INFO] Fetching data for profile: {profile}...")
            
            # Apify Actorによるデータ取得
            run = client.actor("clockworks/tiktok-scraper").call(run_input={
                "profiles": [profile],
                "resultsPerPage": 5
            })
            
            # 取得データのパースと抽出
            for item in client.dataset(run["defaultDatasetId"]).iterate_items():
                play_count = item.get('playCount', 0)
                digg_count = item.get('diggCount', 0)
                
                all_data.append({
                    "user": profile,
                    "text": item.get('text', '')[:30].replace('\n', ' '),
                    "plays": play_count,
                    "likes": digg_count,
                    "engagement_rate": round((digg_count / play_count * 100), 2) if play_count > 0 else 0.0,
                    "url": item.get('webVideoUrl', '')
                })

        except Exception as e:
            print(f"[ERROR] Failed to fetch data for {profile}: {e}")

    # 抽出データのCSV出力
    if all_data:
        df = pd.DataFrame(all_data)
        df.to_csv(RESULT_FILE, index=False, encoding='utf-8-sig')
        print(f"[SUCCESS] {len(all_data)}件のデータを '{RESULT_FILE}' に保存しました。")
    else:
        print("[WARNING] データが取得できませんでした。処理を終了します。")

if __name__ == "__main__":
    analyze_tiktok()