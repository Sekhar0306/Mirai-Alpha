# Category Summary: Equity Mutual Funds

This document explains the SEBI regulations and what to expect in equity fund factsheets.

## SEBI Regulations for Equity Mutual Funds

### Category Classification
SEBI (Securities and Exchange Board of India) has classified mutual funds into specific categories to ensure consistency and comparability:

1. **Equity Funds** - Minimum 65% investment in equities
   - Large Cap Funds
   - Mid Cap Funds
   - Small Cap Funds
   - Multi Cap Funds
   - Flexi Cap Funds
   - ELSS (Equity Linked Savings Scheme)
   - Sectoral/Thematic Funds
   - Value Funds
   - Contra Funds
   - Focused Funds
   - Dividend Yield Funds

2. **Hybrid Funds** - Mix of equity and debt
3. **Debt Funds** - Primarily debt instruments
4. **Solution Oriented Schemes** - Retirement, Children's funds
5. **Other Schemes** - Index funds, ETFs, Fund of Funds

### Key SEBI Rules

1. **Portfolio Concentration Limits**
   - Single stock: Maximum 10% of AUM (can go up to 12% with board approval)
   - Sector limit: Maximum 25% of AUM (can go up to 35% for sectoral funds)
   - Group company limit: Maximum 25% of AUM

2. **Market Cap Definitions** (as of 2021)
   - **Large Cap**: Top 100 companies by market capitalization
   - **Mid Cap**: Companies ranked 101-250
   - **Small Cap**: Companies ranked 251 and below

3. **Disclosure Requirements**
   - Monthly portfolio disclosure within 10 days of month-end
   - Full portfolio disclosure (top 10 holdings + complete list)
   - Sector-wise allocation
   - Asset allocation (equity/debt/cash)

4. **Factsheet Requirements**
   - Must include complete portfolio holdings
   - Sector-wise allocation
   - Asset allocation
   - Top 10 holdings
   - Performance metrics
   - Expense ratio
   - AUM

## Portfolio Construction Expectations

### Typical Holdings Structure

1. **Large Cap Funds**
   - Focus on blue-chip companies
   - Lower volatility
   - Typically 20-40 stocks
   - High liquidity
   - Examples: Reliance, TCS, HDFC Bank, Infosys

2. **Mid Cap Funds**
   - Growth-oriented companies
   - Higher volatility than large cap
   - Typically 30-60 stocks
   - Moderate liquidity
   - Examples: Persistent Systems, Zomato, Page Industries

3. **Small Cap Funds**
   - Emerging companies
   - Highest volatility
   - Typically 50-100+ stocks
   - Lower liquidity
   - Higher diversification required

4. **Multi Cap/Flexi Cap Funds**
   - Mix across market caps
   - Flexible allocation
   - Typically 30-70 stocks
   - Balanced risk-return profile

### Sector Allocation Patterns

**Common Sectors Across Equity Funds:**
- **Financial Services** (20-35%): Banks, NBFCs, Insurance
- **Technology** (10-20%): IT services, Software
- **Consumer Goods** (8-15%): FMCG companies
- **Healthcare** (5-12%): Pharmaceuticals
- **Industrials** (5-10%): Engineering, Infrastructure
- **Energy** (3-8%): Oil & Gas, Power
- **Materials** (3-8%): Cement, Steel, Chemicals
- **Automotive** (3-8%): Auto manufacturers, Ancillaries

## Typical Holdings Styles Across AMCs

### 1. **HDFC Mutual Fund**
- Value-oriented approach
- Long-term holdings
- Focus on quality businesses
- Lower churn rate
- Strong emphasis on financial services

### 2. **ICICI Prudential Mutual Fund**
- Growth-oriented
- Active portfolio management
- Diversified across sectors
- Moderate churn rate

### 3. **SBI Mutual Fund**
- Balanced approach
- Large cap bias
- Government PSU holdings
- Lower expense ratios

### 4. **Axis Mutual Fund**
- Quality growth focus
- Concentrated portfolios
- High conviction bets
- Moderate to high churn

### 5. **Kotak Mahindra Mutual Fund**
- Value investing
- Long-term orientation
- Quality focus
- Lower churn

### 6. **Nippon India Mutual Fund**
- Diversified approach
- Multi-cap strategies
- Balanced sector allocation

### 7. **DSP Mutual Fund**
- Quality and growth
- Research-driven
- Long-term holdings

### 8. **Franklin Templeton Mutual Fund**
- Value investing
- Long-term focus
- Lower turnover

## Data Structure Requirements

For effective analysis, the extracted data must include:

1. **Time-Series Data**: Monthly snapshots for 5 years (60 months)
2. **Cross-AMC Comparison**: Normalized fields across all AMCs
3. **Sector-Level Aggregation**: Consistent sector classification
4. **Security-Level Details**: ISIN, name, quantity, value, percentage
5. **Metadata**: Date, AMC name, fund name

## Common Challenges in Extraction

1. **Table Format Variations**: Different AMCs use different table structures
2. **Multi-Page Holdings**: Holdings spread across multiple pages
3. **Sector Classification**: Inconsistent sector names across AMCs
4. **ISIN Variations**: Different formats or missing ISINs
5. **Scanned PDFs**: Some older factsheets are scanned images
6. **Currency Formatting**: Different number formats (commas, currency symbols)

## Analysis Capabilities Enabled

With properly structured data, we can compute:

1. **Sector Exposure Trends**: How sector allocations changed over time
2. **Top Holdings Analysis**: Most common holdings across funds/AMCs
3. **Churn Analysis**: Turnover of holdings month-over-month
4. **Concentration Risk**: Portfolio concentration metrics
5. **Common Holdings**: Securities held across multiple funds/AMCs
6. **Performance Attribution**: Contribution of holdings to fund performance
7. **Persistence Analysis**: How long securities are held
8. **AMC Comparison**: Compare strategies across different AMCs

