# AI Financial Intelligence — working dashboard + automatic refresh

## What is implemented
- Streamlit company selection and normalized interactive stock performance graphs for **NVIDIA, Alphabet, Apple**.
- SEC companyfacts revenue series displayed **separately** for annual and quarterly reporting periods.
- Official company RSS headline aggregation for **NVIDIA, Alphabet, Apple, OpenAI, Anthropic** (best effort; see failures).
- Interactive company/topic filters, citation links, headline evidence search, JSON export, refresh timestamps, source health/errors.
- GitHub Actions refresh every 6 hours; previous good data retained on individual-source failures.
- Manual refresh button when app host grants filesystem/network access.

## Important limitations
- **Not instantly event-driven:** scheduled updates check for source changes every six hours; GitHub cron runs can be delayed or skipped. The website updates from the new checked-in JSON after the host pulls/redeploys the latest repo commit. The browser may require a refresh.
- **Not a working AI agent/RAG:** evidence explorer is keyword retrieval. Implement an LLM vector database pipeline separately for that rubric requirement. Never claim otherwise.
- **Not guaranteed market data:** yfinance is an unofficial research-only interface and can rate-limit or fail. For reliable licensed prices, replace it with a market-data provider.
- **RSS endpoints may change or return errors**; feeds are monitored and cached entries can be stale.
- Financial data is extracted from public-company SEC filings; private companies do not have comparable standardized public stock/fundamental series.
- SEC quarterly and annual values, fiscal calendars, amended filings and concept definitions require judgment; this is a research aid, not audited reclassification.
- The code itself has not been verified against live APIs in this offline build environment; test collection on your deployed system and examine source-health report.

## Local setup
1. Install Python 3.11+.
2. `pip install -r requirements.txt`
3. Set `SEC_USER_AGENT` to a descriptive agent with a **real contact email** (e.g. `University research Your Name your-email@example.com`) to follow SEC fair-access practices.
4. `python collector.py` — checks all sources, saves `data/snapshot.json`.
5. `streamlit run app.py` — open the URL printed in terminal. Use the Refresh button to collect newer values.

## Automatic refresh, even when your laptop is off
1. Create a GitHub repository and upload **all files, including `.github/workflows/refresh.yml`**.
2. Repository → Settings → Secrets and variables → Actions → New repository secret `SEC_USER_AGENT` with your identification/contact email.
3. Repository → Actions → **Refresh AI industry data** → Run workflow. Check logs and `data/snapshot.json`.
4. Deploy the repo's `app.py` to Streamlit Community Cloud (or another Streamlit host). Configure the host to redeploy on GitHub updates. If necessary refresh the browser for changes.
5. GitHub Actions will attempt an update at 00:17, 06:17, 12:17, and 18:17 UTC. GitHub schedules are best effort and not exact. Review the logs and source-health panel.

## Architecture
GitHub scheduled collector → SEC XBRL + market prices + official RSS → checks/errors → JSON snapshot committed → Streamlit interactive dashboard → research exploration.

## Trustworthy documentation
- SEC APIs: https://www.sec.gov/search-filings/edgar-application-programming-interfaces
- NVIDIA newsroom RSS: https://nvidianews.nvidia.com/rss
- GitHub scheduled workflows: https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax
- yfinance limitations: https://github.com/ranaroussi/yfinance

## Five-minute presentation outline
1. Stakeholder question and the five companies (40 sec).
2. Data architecture, primary sources, data provenance (60 sec).
3. Dashboard stock-price and SEC financial comparisons (85 sec).
4. News announcements, evidence explorer and source health (75 sec).
5. How agentic collection + full RAG would be added; limitations (40 sec).

Be explicit: collectors are automated scripts; they are not autonomous AI agents. Keyword evidence search is not yet LLM RAG.
