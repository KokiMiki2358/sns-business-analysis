# NBA TikTok Data Pipeline & Analysis

TikTokの公開データから最新の投稿を自動収集し、エンゲージメントを可視化するツールです。
ローカルのプロトタイプから、AWSサーバーレス構成（Lambda + S3）へ移行し、自動化とスケーラビリティを確保しています。

## 🚀 Tech & Architecture
- **Language**: Python 3.x
- **Infrastructure**: AWS Lambda (Memory: 512MB, Timeout: 1min), Amazon S3
- **Libraries**: Pandas, Apify API, Matplotlib

## 📊 Core Feature: VRP Labeling
独自の抽出ロジックで、単なる再生数ではなく動画の「質」を評価します。
- **[V] Views**: 拡散力（再生数 上位10%）
- **[R] Rate**: 熱狂度（エンゲージメント率 上位10%）
- **[P] Power**: 影響力（再生数 × 影響率 上位15%）

## 📈 Result (April 2026)
![NBA Analysis Graph](images/2604_nba_analysis.png)

## 🛡️ Security & Data
- 機密情報（APIトークン等）は `.env` および Lambdaの環境変数で隠蔽。
- 大容量の生データ（CSV）は `.gitignore` でリポジトリから除外。

## ⚙️ Quick Start (Local)
```bash
# 1. ライブラリのインストール
pip install pandas python-dotenv apify-client matplotlib

# 2. .env ファイルの作成
echo "APIFY_TOKEN=your_token_here" > .env

# 3. 分析の実行
python src/analysis/analysis.py