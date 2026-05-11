import json
import os
import boto3
import pandas as pd
from apify_client import ApifyClient

def lambda_handler(event, context):
    try:
        # 1. 環境変数からのAPIトークン取得
        apify_token = os.environ.get('APIFY_TOKEN')
        if not apify_token:
            raise ValueError("APIFY_TOKEN is not set in environment variables.")
        
        client = ApifyClient(apify_token)
        
        # 2. データ抽出の実行 (対象: NBA, 取得件数: 30)
        run_input = { "profiles": ["nba"], "resultsPerPage": 30 }
        print(f"[INFO] Starting Apify actor for profiles: {run_input['profiles']}")
        
        run = client.actor("clockworks/tiktok-scraper").call(run_input=run_input)
        
        # 取得したデータセットのリスト化
        results = [item for item in client.dataset(run["defaultDatasetId"]).iterate_items()]
        
        if not results:
            print("[WARNING] No data retrieved from Apify.")
            return {
                'statusCode': 204,
                'body': json.dumps('No data retrieved.')
            }

        # 3. 取得データをPandas DataFrameに変換
        df = pd.DataFrame(results)
        
        # 独自指標「Total ER（総合エンゲージメント率）」の算出
        # いいね(digg) + コメント(comment) + シェア(share) をベースに計算
        df['engagement_rate'] = (df['diggCount'] + df['commentCount'] + df['shareCount']) / df['playCount'] * 100
        df['engagement_rate'] = df['engagement_rate'].fillna(0) # 0除算による欠損値（NaN）を0に補完

        # 4. AWS S3へのCSV出力処理
        s3 = boto3.client('s3')
        bucket_name = 'nba-analysis-data-2358'
        csv_key = 'nba_metrics.csv'
        
        print(f"[INFO] Uploading data to S3 bucket: {bucket_name}/{csv_key}")
        
        # DataFrameをメモリ上でCSV文字列に変換し、S3へPut（一時ファイルを作成しない設計）
        csv_buffer = df.to_csv(index=False, encoding='utf-8-sig')
        s3.put_object(Bucket=bucket_name, Key=csv_key, Body=csv_buffer)
        
        print("[INFO] Lambda execution completed successfully.")
        return {
            'statusCode': 200,
            'body': json.dumps('Data processing and S3 upload completed successfully.')
        }

    except Exception as e:
        print(f"[ERROR] Lambda execution failed: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps(f"Internal Server Error: {str(e)}")
        }