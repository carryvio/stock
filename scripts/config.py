import os
from datetime import datetime

# GitHub 設定
GITHUB_REPO = "carryvio/stock"
DATA_DIR = "data"
OUTPUT_DIR = "data/analysis_output"

# Claude 設定
CLAUDE_MODEL = "claude-3-5-haiku-20241022"
MAX_TOKENS = 2000

# 分析權重
ANALYSIS_SCORES = {
    "技術評分權重": 0.45,
    "籌碼評分權重": 0.35,
    "美股連動權重": 0.20
}

# 關鍵欄位
KEY_COLUMNS = [
    '代號', '名稱', '成交', '漲跌幅',
    'K值(日)', 'D值(日)', 'RSI6(日)', 'RSI12(日)',
    'DIF(日)', 'MACD(日)', '外資買賣超', '投信買賣超',
    '券資比(%)', '5日均線', '20日均線', '60日均線'
]