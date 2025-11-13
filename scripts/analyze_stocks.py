import os
import json
import pandas as pd
import requests
from io import StringIO
from datetime import datetime
from pathlib import Path
import anthropic
from config import *

client = anthropic.Anthropic(api_key=os.environ.get("CLAUDE_API_KEY"))

def get_latest_csv_from_github():
    """從GitHub的data資料夾抓取最新的CSV"""
    try:
        api_url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{DATA_DIR}"
        response = requests.get(api_url)
        response.raise_for_status()
        
        files = response.json()
        
        csv_files = [
            f for f in files 
            if f['name'].startswith('stock_analysis_') and f['name'].endswith('.csv')
        ]
        
        if not csv_files:
            print("❌ 找不到CSV檔案")
            return None, None
        
        latest_file = sorted(csv_files, key=lambda x: x['name'], reverse=True)[0]
        
        raw_url = latest_file['download_url']
        csv_response = requests.get(raw_url)
        csv_response.raise_for_status()
        
        df = pd.read_csv(StringIO(csv_response.text), encoding='utf-8-sig')
        
        print(f"✓ 已從GitHub載入: {latest_file['name']}")
        return df, latest_file['name']
        
    except Exception as e:
        print(f"❌ GitHub抓取失敗: {e}")
        return None, None

def prepare_analysis_data(df: pd.DataFrame) -> str:
    """準備要分析的數據文本"""
    available_cols = [col for col in KEY_COLUMNS if col in df.columns]
    
    if '技術評分' in df.columns:
        df = df[df['技術評分'] > 0].copy()
    
    return df[available_cols].to_string()

def analyze_with_claude(df: pd.DataFrame) -> dict:
    """用Claude分析股票"""
    data_text = prepare_analysis_data(df)
    
    prompt = f"""你是專業台灣股票分析師，使用以下權重評分：
- 技術面：45%（K值、RSI、MACD）
- 籌碼面：35%（外資、投信、券資比）  
- 美股連動：20%（與NVDA/AAPL等的相關性）

分析日期：{datetime.now().strftime('%Y-%m-%d')}

數據：
{data_text}

請以JSON返回分析，包含：
{{
  "stocks": [
    {{
      "代號": "xxxx",
      "名稱": "xxxx",
      "技術評分": 7.5,
      "籌碼評分": 6.0,
      "美股評分": 5.0,
      "綜合評分": 6.3,
      "預測": "偏多/中性/偏弱",
      "預測區間": {{"低": 100, "高": 120}},
      "操作建議": "買進/持有/賣出",
      "理由": "詳細說明"
    }}
  ],
  "市場觀點": "整體市場評論"
}}
"""
    
    try:
        message = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=MAX_TOKENS,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        response_text = message.content[0].text
        
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        
        if json_start >= 0 and json_end > json_start:
            result = json.loads(response_text[json_start:json_end])
            print(f"✓ Claude分析完成，共{len(result.get('stocks', []))}檔股票")
            return result
        
        return {"error": "無法解析回應"}
        
    except Exception as e:
        print(f"❌ Claude API錯誤: {e}")
        return {"error": str(e)}

def save_analysis_result(analysis: dict, source_filename: str):
    """保存分析結果"""
    output_path = Path(OUTPUT_DIR)
    output_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = output_path / f"analysis_{timestamp}.json"
    
    result = {
        "分析時間": datetime.now().isoformat(),
        "源檔案": source_filename,
        "分析結果": analysis
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"✓ 結果已保存: {output_file}")
    return output_file

def main():
    print(f"\n{'='*50}")
    print(f"開始股票分析 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}\n")
    
    df, filename = get_latest_csv_from_github()
    if df is None:
        print("分析中止")
        return
    
    print(f"📊 加載檔案: {filename} ({len(df)} 檔股票)")
    
    analysis = analyze_with_claude(df)
    
    if "error" in analysis:
        print(f"分析失敗: {analysis['error']}")
        return
    
    save_analysis_result(analysis, filename)
    
    print(f"\n✅ 分析完成！")

if __name__ == "__main__":
    main()