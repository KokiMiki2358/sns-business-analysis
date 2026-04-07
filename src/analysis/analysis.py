import os
import pandas as pd
from dotenv import load_dotenv
from apify_client import ApifyClient

# --- 設定（ここを書き換えるだけで対象を増やせる） ---
TARGET_PROFILES = ["nba"] # 将来的にここを ["nba", "fitvalu24", ...] にする
RESULT_FILE = "tiktok_metrics_report.csv"

def analyze_tiktok():
    load_dotenv()
    client = ApifyClient(os.getenv("APIFY_TOKEN"))

    all_data = []

    print(f"--- 抽出開始 (対象: {len(TARGET_PROFILES)}件) ---")

    for profile in TARGET_PROFILES:
        try:
            print(f"Fetching: {profile}...")
            # Apify Actorの呼び出し
            run = client.actor("clockworks/tiktok-scraper").call(run_input={
                "profiles": [profile],
                "resultsPerPage": 5
            })
            
            # データの整形
            for item in client.dataset(run["defaultDatasetId"]).iterate_items():
                play_count = item.get('playCount', 0)
                digg_count = item.get('diggCount', 0)
                
                # 安全にデータを格納
                all_data.append({
                    "user": profile,
                    "text": item.get('text', '')[:30].replace('\n', ' '),
                    "plays": play_count,
                    "likes": digg_count,
                    "engagement": round((digg_count / play_count * 100), 2) if play_count > 0 else 0,
                    "url": item.get('webVideoUrl', '')
                })

        except Exception as e:
            print(f"Error skipping {profile}: {e}")

    # --- 保存処理 ---
    if all_data:
        df = pd.DataFrame(all_data)
        df.to_csv(RESULT_FILE, index=False, encoding='utf-8-sig')
        print(f"\n[SUCCESS] {len(all_data)}件のデータを '{RESULT_FILE}' に保存したぜ。")
    else:
        print("\n[WARNING] データが1件も取得できなかったぜ。")

if __name__ == "__main__":
    analyze_tiktok()