# REFS-PUBLIC.md

External public repositories, datasets, APIs, and documentation that this repo depends on or references.

## FRED API

- **API documentation:** https://fred.stlouisfed.org/docs/api/fred/
- **API key registration:** https://fred.stlouisfed.org/docs/api/api_key.html
- **Series search:** https://fred.stlouisfed.org/
- **FRED release calendar:** https://fred.stlouisfed.org/releases/calendar

## Key FRED Series Referenced

All series in `config/series_catalog.toml`:

| ID | Title | Category |
|----|-------|----------|
| `GDP` | Gross Domestic Product | national_accounts |
| `GDPC1` | Real Gross Domestic Product | national_accounts |
| `UNRATE` | Unemployment Rate | labor_market |
| `PAYEMS` | All Employees, Total Nonfarm | labor_market |
| `CPIAUCSL` | Consumer Price Index for All Urban Consumers: All Items | prices |
| `PCEPI` | Personal Consumption Expenditures: Chain-type Price Index | prices |
| `FEDFUNDS` | Effective Federal Funds Rate | interest_rates |
| `T10Y2Y` | 10-Year Treasury Constant Maturity Minus 2-Year Treasury (Yield Curve Spread) | interest_rates |
| `DGS10` | Market Yield on U.S. Treasury Securities at 10-Year Constant Maturity | interest_rates |
| `MORTGAGE30US` | 30-Year Fixed Rate Mortgage Average | housing |
| `HOUST` | Housing Starts: Total — New Privately Owned Housing Units Started | housing |
| `SP500` | S&P 500 | markets |
| `DCOILWTICO` | Crude Oil Prices: West Texas Intermediate (WTI) | commodities |
| `USREC` | NBER-Based Recession Indicators for the United States | indicators |

## Portfolio Utilities

- `./util-repos/archility` — architecture toolchain bootstrap/render orchestration
- `./util-repos/dyno-lab` — portfolio-standard test bench utilities
