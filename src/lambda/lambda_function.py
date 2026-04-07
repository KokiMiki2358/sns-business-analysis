import json
import os
import boto3  # AWSを操作する魔法のライブラリ
import pandas as pd
from apify_client import ApifyClient

def lambda_handler(event, context):
    # 1. 環境変数からトークンを取得（さっき設定したやつ！）
    apify_token = os.environ['APIFY_TOKEN']
    client = ApifyClient(apify_token)
    
        # 2. スクレイピング実行（ここで df を作る！）
    run_input = { "profiles": ["nba"], "resultsPerPage": 30 } # 検索条件
    
    # 実際にApifyを叩いてデータを取る
    run = client.actor("clockworks/tiktok-scraper").call(run_input=run_input)
    
    # 取ってきたデータをリストにする
    results = [item for item in client.dataset(run["defaultDatasetId"]).iterate_items()]
    
    # 🌟 ここが重要！リストをPandasの「df」という名前に変換する
    df = pd.DataFrame(results)
    
    df['engagement_rate'] = (df['diggCount'] + df['commentCount'] + df['shareCount']) / df['playCount'] * 100
    df['engagement_rate'] = df['engagement_rate'].fillna(0) # 0除算対策

    # 3. S3に保存する（ここがクラウド流！）
    s3 = boto3.client('s3')
    bucket_name = 'nba-analysis-data-2358' # さっき作ったバケット名
    csv_key = 'nba_metrics.csv'
    
    # DataFrameをCSV文字列に変換してS3へ
    csv_buffer = df.to_csv(index=False)
    s3.put_object(Bucket=bucket_name, Key=csv_key, Body=csv_buffer)
    
    return {
        'statusCode': 200,
        'body': json.dumps('分析完了してS3に保存したぜ！')
    }