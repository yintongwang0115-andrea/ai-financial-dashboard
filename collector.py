"""Collect fresh official SEC financial facts, official newsroom RSS, and market data.
No fabricated fallback values; errors surface in the dashboard.
"""
import os, json, re, time
from datetime import datetime, timezone, timedelta
from pathlib import Path
import requests
import feedparser
import pandas as pd
import yfinance as yf

BASE=Path(__file__).resolve().parent
DATA=BASE/'data'
COMPANIES={
 'NVIDIA': {'ticker':'NVDA','cik':'0001045810','site':'https://investor.nvidia.com/','product':'Blackwell, GPUs, AI infrastructure'},
 'Alphabet': {'ticker':'GOOGL','cik':'0001652044','site':'https://abc.xyz/investor/','product':'Gemini, Google Cloud, AI Search'},
 'Apple': {'ticker':'AAPL','cik':'0000320193','site':'https://investor.apple.com/','product':'Apple Intelligence, Siri, on-device AI'},
 'OpenAI': {'ticker':None,'cik':None,'site':'https://openai.com/news/','product':'ChatGPT, GPT models, API'},
 'Anthropic': {'ticker':None,'cik':None,'site':'https://www.anthropic.com/news','product':'Claude, Claude API'},
}
RSS={
 'NVIDIA':'https://nvidianews.nvidia.com/rss.xml',
 'Apple':'https://www.apple.com/newsroom/rss-feed.rss',
 'OpenAI':'https://openai.com/news/rss.xml',
 'Anthropic':'https://www.anthropic.com/rss.xml',
 'Alphabet':'https://blog.google/rss/',
}
HEADERS={'User-Agent':os.getenv('SEC_USER_AGENT','University student research dashboard student-research contact example@example.com'),'Accept-Encoding':'gzip, deflate','Host':'data.sec.gov'}
REVENUE_TAGS=['RevenueFromContractWithCustomerExcludingAssessedTax','Revenues','SalesRevenueNet','RevenueFromContractWithCustomerIncludingAssessedTax']

def get_json(url, headers=None):
 r=requests.get(url,headers=headers or {'User-Agent':'AI Research Academic Dashboard/1.0'},timeout=25)
 r.raise_for_status()
 return r.json()

def sec_financials(cik):
 raw=get_json(f'https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json',HEADERS)
 facts=raw.get('facts',{}).get('us-gaap',{})
 candidates=[]
 for tag in REVENUE_TAGS:
  for p in facts.get(tag,{}).get('units',{}).get('USD',[]):
   if p.get('form') not in ['10-K','10-Q'] or not p.get('start') or not p.get('end'): continue
   try: duration=(datetime.fromisoformat(p['end'])-datetime.fromisoformat(p['start'])).days
   except ValueError: continue
   if duration<70 or duration>380 or 'val' not in p: continue
   # fiscal quarter vs full fiscal year: never compare as equivalent
   period='annual' if duration>=300 else 'quarterly' if duration<=110 else 'other'
   if period=='other': continue
   candidates.append({'end':p['end'],'start':p['start'],'filed':p.get('filed',''),'form':p['form'],'fy':p.get('fy'),'fp':p.get('fp'),'value':p['val'],'tag':tag,'period':period,'accession':p.get('accn','')})
 # prefer best tag; retain as-filed revisions and select latest filed for each duration interval
 priority={t:i for i,t in enumerate(REVENUE_TAGS)}
 candidates.sort(key=lambda x:(priority[x['tag']],x['filed']),reverse=False)
 unique={}
 for x in candidates:
  key=(x['start'],x['end'],x['period'])
  if key not in unique or (priority[x['tag']], -int(x['filed'].replace('-','') or 0)) < (priority[unique[key]['tag']],-int(unique[key]['filed'].replace('-','') or 0)):
   unique[key]=x
 return sorted(unique.values(),key=lambda x:x['end'],reverse=True)[:45]

def stock_prices(ticker):
 df=yf.Ticker(ticker).history(period='1y',interval='1d',auto_adjust=True)
 if df is None or df.empty: raise ValueError('No price history returned')
 return [{'date':str(k.date()),'close':round(float(v),4)} for k,v in df['Close'].dropna().items()]

def official_news(name):
 url=RSS[name]
 feed=feedparser.parse(url,request_headers={'User-Agent':'AI Industry Student Research Dashboard/1.0'})
 if feed.bozo and not feed.entries: raise RuntimeError(f'RSS unavailable or invalid: {url}')
 out=[]
 for e in feed.entries[:35]:
  link=e.get('link',''); title=re.sub('<[^>]*>','',e.get('title','')).strip()
  if not (link.startswith('https://') and title): continue
  date=e.get('published',e.get('updated',''))
  out.append({'company':name,'title':title,'url':link,'published':date,'source_feed':url})
 if not out: raise RuntimeError(f'Feed returned no items: {url}')
 return out

def collect():
 DATA.mkdir(exist_ok=True)
 now=datetime.now(timezone.utc).isoformat()
 data={'retrieved_at':now,'companies':COMPANIES,'stocks':{},'revenue':{},'news':{},'status':{}}
 for name,info in COMPANIES.items():
  if info['ticker']:
   try:
    data['stocks'][name]=stock_prices(info['ticker'])
    data['status'][name+' stock']='ok'
   except Exception as e: data['status'][name+' stock']='ERROR: '+str(e)[:180]
  if info['cik']:
   try:
    data['revenue'][name]=sec_financials(info['cik'])
    data['status'][name+' SEC']='ok' if data['revenue'][name] else 'No revenue facts found'
   except Exception as e: data['status'][name+' SEC']='ERROR: '+str(e)[:180]
  try:
   data['news'][name]=official_news(name)
   data['status'][name+' RSS']='ok'
  except Exception as e: data['status'][name+' RSS']='ERROR: '+str(e)[:180]
  time.sleep(.15)
 # Do not silently overwrite a successful source with a transient failed refresh
 path=DATA/'snapshot.json'
 if path.exists():
  try:
   old=json.loads(path.read_text())
   for category in ('stocks','revenue','news'):
    for name,val in old.get(category,{}).items():
     if not data[category].get(name): data[category][name]=val
  except Exception: pass
 path.write_text(json.dumps(data,indent=2,ensure_ascii=False))
 return data

if __name__=='__main__':
 result=collect()
 print('Updated',result['retrieved_at']); print('\n'.join(f'{k}: {v}' for k,v in result['status'].items()))
