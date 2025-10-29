# PE Portfolio Monitoring Dashboard

## Project Setup

### 1. Create Virtual Environment & Install Dependencies
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Set Up Local Database
Create a `.env` file based on `.env.sample` and fill in your desired values.

Start the database with Docker:
```bash
docker compose up -d
```

Populate the database:
```bash
cd raw_data
python etl_load_data.py
cd ..
```

### 3. Reset Database (if needed)
```bash
docker compose down
rm -rf pgdata
docker compose up -d
cd raw_data && python etl_load_data.py
cd ..
```

### 4. Run DBT Transformations
```bash
cd dbt_pe
dbt build
cd ..
```

### 5. Launch Dashboard
```bash
cd pe_dashboard
streamlit run main.py
```

---

## Dashboard Overview

The dashboard provides two main views:

1. **Fund Overview** - Portfolio-wide metrics with invested company specifics
2. **Company Deep Dive** - Detailed analysis of individual companies including financials, trends, budget variance, KPIs, and risk flags

---

## Key Selections & Assumptions

### Technology Stack
- **Database**: Local PostgreSQL (for quick development and data structure control)
- **Data Transformation**: dbt (enables version-controlled, documented transformations)
- **Dashboard**: Streamlit (lightweight, free, suitable for proof of concept)

### Data Conventions
- **Currency**: All amounts in EUR millions
- **Date Convention**: Monthly data uses first day of month (e.g., 2023-01-01)
- **Fiscal Year**: Calendar year (January 1 - December 31) for all companies

### Budget Spreading Methodology
- **Annual budgets spread evenly across 12 months** (Annual Budget / 12)
- Assumes no seasonal patterns due to lack of historical data
- Future enhancement could incorporate seasonality weights if data becomes available

### Financial Calculations
- **Month-over-Month (MoM)**: `((Current - Previous) / Previous) × 100`
- **Year-over-Year (YoY)**: `((Current - Same Month Last Year) / Same Month Last Year) × 100`
- **Last Twelve Months (LTM)**: Rolling 12-month sum for metrics
- **Year-to-Date (YTD)**: Sum from January to current month
- **EBITDA Margin**: `(EBITDA / Revenue) × 100`
- **Net Leverage**: `Net Debt / LTM EBITDA` - Quick view of financial risk: how many years of EBITDA at current pace to pay off net debt.
- **Cash Conversion**: `(Cash from Operations / EBITDA) × 100` - Measures quality of earnings - how much EBITDA converts to actual cash

### Key Metrics & Risk Monitoring

Focused on company C001 (NordicFiber AB).

**Dashboard Metric Rationale:**

Core metrics selected to answer key PE investor questions:
- **Revenue + MoM/YoY Growth**: Business trajectory and momentum tracking
- **EBITDA + Margin %**: Operational performance and efficiency
- **Net Leverage Ratio**: Exit readiness
- **Cash Conversion %**: Quality of earnings - ensures EBITDA translates to actual cash
- **Gross Profit + Margin %**: Monitors pricing power and COGS management
- **OpEx % of Revenue**: Tracks operating leverage and cost scalability

**Visualization Choices:**
- 12-month financial table: Comprehensive historical view for trend identification
- Dual-axis charts: Show absolute metrics alongside efficiency ratios in single view
- Budget variance analysis: Monitors deviation from investment thesis (YTD focus = cumulative performance)

**Risk Flag Thresholds:**
- **Revenue Risk**: Decline > 10% MoM (business momentum concern)
- **Profitability Risk**: EBITDA Margin compression > 200 bps (operational efficiency issue)
- **Leverage Risk**: Net Debt / EBITDA > 5.0x (exit constraint risk)
- **Liquidity Risk**: Cash Conversion < 70% for 3 consecutive months (working capital or collection issue)
- **Budget Variance Risk**: YTD Revenue variance < -15% (significant underperformance)


### KPI Analysis by Industry
Different companies track industry-specific KPIs:
- **Telecom/Broadband**: Homes Passed, ARPU (€/month), Churn Rate (%)
- KPIs are monitored for trends and anomalies (> 2 standard deviations from 6-month mean)
- **Churn Risk (Telecom/Broadband companies)**: Monthly churn rate > 2.5%
  - Industry benchmark: 1-2% is typical for broadband
  - Used to flag companies requiring deeper investigation

---

## Data Transformation Layers

1. **Staging Layer** - Metric calculations, budget spreading
2. **Marts Layer** - Dashboard-ready aggregated views optimised for visualisation

---

## Known Limitations

### Data
- Limited to 2 years of historical data (2023-2025)
- Even budget spread doesn't account for seasonality
- No external benchmarking or supplementary data sources

### Future Enhancements
- Transfer to Power BI for increased functionality and customisation
- Focus on investment-level analysis (fund-specific performance tracking to measure metrics such as IRR or MOIC)
- Add dynamic date filters and enhanced data manipulation
- Incorporate historical seasonality patterns for budget spreading
- Include forward-looking projections
- Include separate pages on the dashboard for areas of particular focus (certain analysts may prioritise specific metrics for analysis)


## Company Analysis: NordicFiber AB (C001)

### Financial Performance

**Revenue**
Revenue growth is strong YoY, indicating a stable growth trajectory. Although, we can see monthly swings, suggesting volatility in order timing rather than structural weakness. Revenue has recently exceeded budget, showing outperformance vs plan after a slower start to the year.

**Profitability**
Gross margin is high and stable which indicates strong pricing power.

EBITDA growth is outpacing revenue growth which indicates that the business is becoming more efficient at making profit. Recent performance beat budget, reflecting better than expected efficiency. As EBITDA margin is increasing, the company is scaling profitably.

### Operational Metrics

**Cash & Leverage**
Cash conversion is strong and stable which supports reinvestment.

Net leverage ratio is improving 4.01 to 3.26 over the period. This indicates that the business is reducing debt which lowers risk and borrowing costs.

### Key Performance Indicators

- **Network Expansion**: Homes passed grew from 1,620k to 2,150k showing that they are investing in infrastructure and reaching more customers
- **ARPU**: What each customer pays monthly increased over the period indicating that they can raise prices without losing customers
- **Churn Rate**: Improved from 6.2% to 5.4%. Fewer customers are leaving which is a sign of good service and competitive position. However the figure is still above the 2.5% risk threshold, but trending in the right direction

### Summary Assessment

This business is delivering high-margin, profitable growth with strong YoY revenue and EBITDA expansion. There is also continuous deleveraging improving financial resiliency. Internal initiatives have also reduced customer churn and ensured company expansion. Need to monitor churn levels to assess whether they continue to drop.
