import json, os
from pathlib import Path
from datetime import datetime, timezone
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from collector import COMPANIES, collect

st.set_page_config(page_title='AI Financial Intelligence',page_icon='📈',layout='wide')
st.markdown('''<style>.block-container{padding-top:1.5rem;max-width:1480px} div[data-testid="stMetric"]{background:#18223410;padding:1rem;border:1px solid #7891a22b;border-radius:12px}.smallnote{color:#7a8598;font-size:.84rem}</style>''',unsafe_allow_html=True)
DATA=Path(__file__).parent/'data'/'snapshot.json'

def load():
 if not DATA.exists(): return None
 try: return json.loads(DATA.read_text())
 except Exception: return None

st.title('◈ AI Financial Intelligence')
st.caption('US AI corporations • Product innovation × financial performance × investor response')
with st.sidebar:
 st.header('Research controls')
 names=st.multiselect('Companies',list(COMPANIES),default=list(COMPANIES))
 timeframe=st.selectbox('Price history', ['1 month','3 months','6 months','1 year'],index=3)
 st.divider()
 st.subheader('Refresh policy')
 st.write('Scheduled GitHub refresh: every 6 hours. Manual refresh runs data collection in the app when permitted by the host.')
 if st.button('↻ Fetch newest data now',use_container_width=True):
  with st.spinner('Querying the source APIs...'):
   try: collect();st.success('Data collection completed. Review source status for any errors.');st.rerun()
   except Exception as e: st.error(f'Collection error: {e}')
 st.caption('Market data may be delayed. SEC filings update when new reports are filed; announcements appear when source feeds update.')

snapshot=load()
if snapshot is None:
 st.warning('No snapshot available yet. Run `python collector.py` or use **Fetch newest data now**. No numbers are invented.')
 st.stop()

stamp=snapshot.get('retrieved_at')
st.caption(f'Last collector run: **{stamp or "unknown"}** · Every number links to its underlying data source where available.')
if stamp:
 try:
  age=(datetime.now(timezone.utc)-datetime.fromisoformat(stamp)).total_seconds()/3600
  if age>8: st.warning(f'Data is {age:.1f} hours old. Scheduled refresh may be delayed; inspect Source Health.')
 except Exception: pass

main,events,financial,assistant,sources=st.tabs(['📈 Market overview','🧠 AI announcements','📑 SEC financials','🔎 Evidence explorer','🩺 Source health'])

with main:
 st.subheader('Normalized stock performance')
 st.caption('Adjusted daily close, rebased to 100 at the first displayed trading day; compares relative return, not share price. OpenAI and Anthropic are private and have no public stock series.')
 months={'1 month':30,'3 months':90,'6 months':180,'1 year':365}[timeframe]
 parts=[]
 for name in names:
  prices=snapshot.get('stocks',{}).get(name,[])
  if not prices: continue
  df=pd.DataFrame(prices);df['date']=pd.to_datetime(df['date']);df=df.sort_values('date');cutoff=df['date'].max()-pd.Timedelta(days=months)
  df=df[df['date']>=cutoff].copy()
  if len(df)>1 and df['close'].iloc[0]>0:
   df['index']=df['close']/df['close'].iloc[0]*100;df['company']=name;parts.append(df)
 if parts:
  stocks=pd.concat(parts)
  fig=px.line(stocks,x='date',y='index',color='company',labels={'index':'Adjusted price index (start = 100)','date':'Trading day'},template='plotly_white')
  fig.update_layout(height=440,legend_title_text='',hovermode='x unified')
  st.plotly_chart(fig,use_container_width=True)
  cards=st.columns(min(len(parts),3))
  for i,d in enumerate(parts):
   chg=(d['close'].iloc[-1]/d['close'].iloc[0]-1)*100
   cards[i%len(cards)].metric(d['company'].iloc[0]+' return',f'{chg:+.2f}%',f'{len(d)} trading sessions')
 else: st.info('No usable market prices returned for selected companies.')
 st.markdown('**Data method:** Price data is requested through the community-maintained `yfinance` interface, for educational research; it is not an official exchange market-data feed. [Provider information](https://github.com/ranaroussi/yfinance).')

with events:
 st.subheader('Official company announcements')
 st.caption('Headlines are retrieved automatically from official feeds when available. A headline appearing near a price change does not prove causation.')
 rows=[n for comp in names for n in snapshot.get('news',{}).get(comp,[])]
 keyword=st.text_input('Filter headlines by topic',placeholder='e.g. model, chip, data center, partnership')
 if keyword: rows=[r for r in rows if keyword.casefold() in r['title'].casefold()]
 for row in rows[:80]:
  st.markdown(f'**{row["company"]}** · {row.get("published") or "Publication date unavailable"}  \n[{row["title"]}]({row["url"]})')
  st.divider()
 if not rows: st.info('No matching news in the latest feed snapshot. Check Source Health.')

with financial:
 st.subheader('Reported company revenue — SEC XBRL')
 st.caption('Annual (≈12 months) and quarterly (≈3 months) periods must never be directly combined. SEC reported values may be restated; both reporting period and filing date are shown.')
 period=st.radio('Reporting period',['annual','quarterly'],horizontal=True)
 latest=[]
 for name in names:
  items=[x for x in snapshot.get('revenue',{}).get(name,[]) if x['period']==period]
  if items:
   x=items[0];latest.append({'company':name,'Revenue ($B)':x['value']/1e9,'Period ending':x['end'],'Filed':x['filed'],'Accounting concept':x['tag']})
 if latest:
  f=pd.DataFrame(latest)
  fig=px.bar(f,x='company',y='Revenue ($B)',text_auto='.2f',template='plotly_white',hover_data=['Period ending','Filed','Accounting concept'])
  fig.update_layout(height=400)
  st.plotly_chart(fig,use_container_width=True)
  st.dataframe(f,use_container_width=True,hide_index=True)
  st.warning('Companies have different fiscal calendars. Revenue figures may use different accounting concepts or periods. Review context before comparing.')
 else: st.info('No SEC revenue entries were retrieved for these companies/period.')
 st.markdown('**Audit sources:** [SEC companyfacts API](https://www.sec.gov/search-filings/edgar-application-programming-interfaces) · '+ ' · '.join(f'[{n} filings](https://data.sec.gov/api/xbrl/companyfacts/CIK{info["cik"]}.json)' for n,info in COMPANIES.items() if n in names and info['cik']))
 st.info('OpenAI and Anthropic do not report standardized public-company stock and SEC revenue series comparable with these three listed companies.')

with assistant:
 st.subheader('Evidence explorer — source-grounded research')
 st.caption('This is a transparent keyword-based retrieval prototype, NOT an LLM-powered RAG system. It shows cited source matches and suggested research checks instead of generating unsupported conclusions.')
 q=st.text_input('Research question or keywords',placeholder='How does Blackwell affect NVIDIA?')
 if q:
  tokens=set(w.lower() for w in q.split() if len(w)>3)
  corpus=[r for comp in names for r in snapshot.get('news',{}).get(comp,[])]
  scored=[]
  for item in corpus:
   title=item['title'].lower();score=sum(t.strip('?!.,') in title for t in tokens)
   if item['company'].lower() in q.lower():score+=2
   if score:scored.append((score,item))
  scored.sort(key=lambda item:-item[0])
  if scored:
   st.write(f'{len(scored)} relevant official-source headlines found. Top matches:')
   for _,r in scored[:8]: st.markdown(f'- **{r["company"]}:** [{r["title"]}]({r["url"]}) · {r.get("published", "") or "date unavailable"}')
   st.info('Suggested analysis: identify the product and announcement date, inspect company filings for reported revenue impact, and compare adjusted stock returns before and after the announcement. Control for concurrent earnings and market-wide news.')
  else:st.info('No matching evidence in current official feed snapshot. Broaden keywords or refresh sources.')
 st.markdown('**To upgrade to actual RAG:** ingest full source documents → chunk and index text → retrieve relevant passages → ask an LLM to answer from passages only → return passage-level citations and confidence/abstention.')

with sources:
 st.subheader('Source health & provenance')
 statuses=snapshot.get('status',{})
 if statuses:
  st.dataframe(pd.DataFrame([{'Source':k,'Status':v} for k,v in statuses.items()]),use_container_width=True,hide_index=True)
  bad={k:v for k,v in statuses.items() if v!='ok'}
  if bad:st.error(f'{len(bad)} source(s) failed or returned no fresh data. Existing cached content may be shown; it is NOT independently confirmed fresh.')
 st.markdown('**Official-source URLs**')
 for name in names:
  info=COMPANIES[name]
  st.markdown(f'- **{name}:** [corporate/investor website]({info["site"]}) · [news feed]({snapshot.get("news",{}).get(name,[{}])[0].get("source_feed", "https://www.sec.gov/") if snapshot.get("news",{}).get(name) else "https://www.sec.gov/"})')
 st.markdown('---')
 st.write('**Data integrity:** Source failures are logged; previous cached content is retained for continuity but must be treated as potentially stale. This application does not claim causation, real-time quotes, or verified private-company revenue.')
 st.download_button('Download current snapshot JSON',json.dumps(snapshot,indent=2),file_name='ai_source_snapshot.json',mime='application/json')

st.divider()
st.caption('Academic research dashboard · Financial information is for analysis, not investment advice · Collection schedule depends on successful GitHub Actions runs and deployment configuration.')
