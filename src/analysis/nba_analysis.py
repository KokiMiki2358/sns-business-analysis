import os
import re
import datetime
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import japanize_matplotlib

from dotenv import load_dotenv
from apify_client import ApifyClient

# ==========================================
# 分析パラメータおよび出力設定
# ==========================================
TARGET_PROFILES = ["nba"]
FETCH_COUNT = 50
PROJECT_NAME = "nba_strategic_audit"

# 実行日時に基づく出力ファイル名の動的生成
now = datetime.datetime.now().strftime('%Y%m%d_%H%M')
RESULT_FILE = f"{PROJECT_NAME}_{now}.csv"
GRAPH_FILE_MAIN = f"{PROJECT_NAME}_{now}_Main.png"
GRAPH_FILE_DEEPDIVE = f"{PROJECT_NAME}_{now}_DeepDive_TotalER.png"

# ==========================================
# ユーティリティ関数
# ==========================================

def extract_safe_japanese(text):
    """
    Matplotlibでの描画エラーや文字化けを防ぐためのテキストサニタイズ処理。
    許可された文字（英数字、平仮名、片仮名、漢字、特定の記号）のみを抽出する。
    """
    safe_text = re.sub(r'[^\w\sぁ-んァ-ン一-龥ー!！?？.。「」【】()（）]', '', text)
    safe_text = re.sub(r'\s+', ' ', safe_text)
    return safe_text.strip()

# ==========================================
# 可視化処理 (メインダッシュボード)
# ==========================================

def create_main_graph(df):
    """
    再生数とエンゲージメント率の相関を可視化する散布図ダッシュボードを生成。
    特筆すべき指標（Score, View, Engagement）の上位動画をハイライトして表示する。
    """
    # 描画領域の初期化 (左: グラフ領域, 右: 動画リスト領域)
    fig = plt.figure(figsize=(20, 9))
    ax_graph = fig.add_axes([0.05, 0.1, 0.45, 0.8]) 
    ax_legend1 = fig.add_axes([0.52, 0.1, 0.23, 0.8]) 
    ax_legend2 = fig.add_axes([0.76, 0.1, 0.23, 0.8]) 
    
    ax_legend1.axis('off')
    ax_legend2.axis('off')
    
    # 独自指標（Score）の算出および上位インデックスの抽出
    df['score'] = df['plays'] * df['engagement'] 
    top_s = df.nlargest(3, 'score').index.tolist()
    top_v = df.nlargest(3, 'plays').index.tolist()
    top_e = df.nlargest(3, 'engagement').index.tolist()
    
    # 散布図および凡例用のラベル生成
    plot_labels = []
    for i, index in enumerate(df.index):
        overall_num = i + 1 
        badges = []
        
        if index in top_s: badges.append(f"[S{top_s.index(index) + 1}]")
        if index in top_v: badges.append(f"[V{top_v.index(index) + 1}]")
        if index in top_e: badges.append(f"[E{top_e.index(index) + 1}]")
            
        if badges:
            full_badge = "".join(badges)
            plot_labels.append(f"{full_badge}-{overall_num}")
        else:
            plot_labels.append(str(overall_num))
            
    df['plot_label'] = plot_labels 
    
    # 散布図の描画
    sns.scatterplot(data=df, x='plays', y='engagement', color='darkorange', s=100, ax=ax_graph)
    ax_graph.set_title(f'TikTok Engagement Analysis: {TARGET_PROFILES[0]}', fontsize=16, weight='bold')
    ax_graph.set_xlabel('Play Count (Views)')
    ax_graph.set_ylabel('Engagement Rate (Likes/Views %)')
    ax_graph.grid(True)
    
    # プロットへのラベル付与（重要指標は強調表示）
    for _, row in df.iterrows():
        is_special = row['plot_label'].startswith('[')
        ax_graph.annotate(
            row['plot_label'],
            (row['plays'], row['engagement']),
            xytext=(6, 6),
            textcoords='offset points',
            fontsize=10 if is_special else 9, 
            color='blue' if is_special else 'black',
            weight='bold' if is_special else 'normal'
        )
        
    # 動画リスト（テキスト凡例）の構築
    list_text1 = "【S】Score TOP / 【V】View TOP / 【E】Likes TOP\n\n"
    list_text2 = " \n\n"
    
    for i, row in df.iterrows():
        # URLから末尾のIDを抽出 (欠損値対策含む)
        video_id = str(row['url']).split('/')[-1][-4:] if pd.notnull(row['url']) else "----"
        plays_fmt = f"{int(row['plays']):,}"
        
        # タイトルのサニタイズと文字数制限
        safe_title = extract_safe_japanese(row['text'])
        short_title = safe_title[:15] + ".." if len(safe_title) > 15 else safe_title
        
        line = f"{row['plot_label']:<12} ID:{video_id} ({plays_fmt:>7} views) : {short_title}\n"
        
        if i < 25: 
            list_text1 += line
        else: 
            list_text2 += line
            
    # テキスト凡例の描画
    ax_legend1.text(0, 1, list_text1, fontsize=10, va='top')
    ax_legend2.text(0, 1, list_text2, fontsize=10, va='top')
    
    plt.savefig(GRAPH_FILE_MAIN, format='png', bbox_inches='tight', dpi=150)

# ==========================================
# 深掘り分析ダッシュボード (Total ER基軸)
# ==========================================
def create_deepdive_graphs_total_er(df):
    """
    動画長、投稿時間(JST)、音源などの各種メタデータと
    総合エンゲージメント率(Total ER)の相関を可視化するダッシュボード。
    """
    fig, axes = plt.subplots(1, 3, figsize=(24, 7))
    
    # 1. 動画長 vs 総合エンゲージメント率 (散布図)
    sns.scatterplot(data=df, x='duration_sec', y='total_er', color='teal', s=80, ax=axes[0])
    axes[0].set_title('1. Duration vs Total Engagement Rate', fontsize=14, weight='bold')
    axes[0].set_xlabel('Duration (Seconds)')
    axes[0].set_ylabel('Total Engagement Rate (%)')
    axes[0].grid(True)
    
    # 2. 曜日 × 時間帯 のエンゲージメントヒートマップ (JST)
    # タイムゾーンをUTCから日本時間(JST)へ変換
    df['create_time'] = pd.to_datetime(df['createTimeISO'], utc=True)
    df['create_time_jst'] = df['create_time'].dt.tz_convert('Asia/Tokyo')
    df['day_of_week'] = df['create_time_jst'].dt.day_name()
    df['hour'] = df['create_time_jst'].dt.hour
    
    # ヒートマップ用のクロス集計 (曜日×時間帯別の平均Total ER)
    heatmap_data = df.pivot_table(index='day_of_week', columns='hour', values='total_er', aggfunc='mean')
    order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    heatmap_data = heatmap_data.reindex(order)
    
    sns.heatmap(heatmap_data, cmap='YlOrRd', annot=True, fmt=".1f", linewidths=.5, ax=axes[1])
    axes[1].set_title('2. Engagement Heatmap by Day & Hour (JST)', fontsize=14, weight='bold')
    axes[1].set_xlabel('Hour of Day (0-23)')
    axes[1].set_ylabel('Day of the Week')
    
    # 3. 使用音源別の平均総合エンゲージメント率 Top5
    music_er_total = df.groupby('music')['total_er'].mean().nlargest(5).reset_index()
    # 視認性向上のため長い音源名を丸める
    music_er_total['music_short'] = music_er_total['music'].apply(lambda x: x[:15] + ".." if len(x) > 15 else x)
    
    sns.barplot(data=music_er_total, x='total_er', y='music_short', ax=axes[2], palette='viridis')
    axes[2].set_title('3. Top 5 Audio Tracks by Avg Total ER', fontsize=14, weight='bold')
    axes[2].set_xlabel('Avg Total Engagement Rate (%)')
    axes[2].set_ylabel('')
    
    plt.tight_layout()
    plt.savefig(GRAPH_FILE_DEEPDIVE, format='png', bbox_inches='tight', dpi=150)

# ==========================================
# メイン実行パイプライン
# ==========================================
def analyze_tiktok():
    """
    Apify経由でのデータ抽出(Extract)、Pandasを用いたデータ加工・指標算出(Transform)、
    およびCSV/グラフ画像としての出力(Load)を担う一連のETL処理。
    """
    load_dotenv()
    client = ApifyClient(os.getenv("APIFY_TOKEN"))
    all_data = []

    print(f"[INFO] Analysis started for target: {TARGET_PROFILES[0]}")

    for profile in TARGET_PROFILES:
        try:
            # Apifyクローラーの実行
            run = client.actor("clockworks/tiktok-scraper").call(run_input={
                "profiles": [profile],
                "resultsPerPage": FETCH_COUNT
            })
            
            # データセットからの必要項目の抽出
            for item in client.dataset(run["defaultDatasetId"]).iterate_items():
                play_count = item.get('playCount', 0)
                digg_count = item.get('diggCount', 0)
                comment_count = item.get('commentCount', 0)
                share_count = item.get('shareCount', 0)
                save_count = item.get('collectCount', 0)
                
                all_data.append({
                    "user": profile,
                    "createTimeISO": item.get('createTimeISO', ''),
                    "text": item.get('text', '')[:50].replace('\n', ' '),
                    "plays": play_count,
                    "likes": digg_count,
                    "comments": comment_count,
                    "shares": share_count,
                    "saves": save_count,
                    "total_er": round(((digg_count + comment_count + share_count + save_count) / play_count * 100), 2) if play_count > 0 else 0.0,
                    "engagement": round((digg_count / play_count * 100), 2) if play_count > 0 else 0.0,
                    "duration_sec": item.get('videoMeta', {}).get('duration', 0),
                    "music": item.get('musicMeta', {}).get('musicName', 'Unknown'),
                    "url": item.get('webVideoUrl', '')
                })
        except Exception as e:
            print(f"[ERROR] Failed to fetch data for {profile}: {e}")

    if all_data:
        # データフレームの作成とソート
        df = pd.DataFrame(all_data)
        df = df.sort_values(by='engagement', ascending=False).reset_index(drop=True)
        
        # 可視化処理の実行
        create_main_graph(df)
        create_deepdive_graphs_total_er(df)
        
        # CSV出力向けの前処理 (JSTタイムゾーン情報等の付与)
        df['create_time'] = pd.to_datetime(df['createTimeISO'], utc=True)
        df['create_time_jst'] = df['create_time'].dt.tz_convert('Asia/Tokyo')
        df['day_of_week'] = df['create_time_jst'].dt.day_name()
        df['hour'] = df['create_time_jst'].dt.hour
        # 中間生成された日時オブジェクト列のクレンジング
        df = df.drop(columns=['create_time', 'create_time_jst']) 
        
        df.to_csv(RESULT_FILE, index=False, encoding='utf-8-sig')
        
        print(f"[SUCCESS] Analysis pipeline completed.")
        print(f"[INFO] CSV file generated: {RESULT_FILE}")
        print(f"[INFO] Main Chart generated: {GRAPH_FILE_MAIN}")
        print(f"[INFO] DeepDive Chart generated: {GRAPH_FILE_DEEPDIVE}")
    else:
        print("[WARNING] No data retrieved. Process terminated.")

if __name__ == "__main__":
    analyze_tiktok()