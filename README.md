Markdown
# 📈 NIFTY Quantitative Screener & Portfolio Engine

This is an institutional-grade quantitative portfolio engine and stock screener built in Python. It evaluates Indian equities (NIFTY) based on a 5-factor model (Momentum, Quality, Growth, Risk, and Risk-Adjusted Returns). 

The system includes a zero look-ahead bias backtester, accounts for realistic institutional trading friction (30 bps), uses dynamic 10Y Indian G-Sec yields for risk-free rate calculations, and features a fully interactive web dashboard.

## 🚀 Quick Start Guide (macOS & Linux)

Follow these step-by-step instructions to set up and run the project on any macOS or Linux machine.

### Step 1: Install System Prerequisites
**For Linux (Ubuntu/Debian) users only:**
You may need to install standard Python and Git tools first. Open your terminal and run:
Bash
sudo apt update
sudo apt install git python3-pip python3-venv -y
(Note: macOS users can skip this step as Python and Git are typically pre-installed or available via Xcode Command Line Tools / Homebrew).

###Step 2: Clone the Repository
Download the project to your local machine and navigate into the folder:
Bash
git clone [https://github.com/nishachar90/nifty_quant_screener.git](https://github.com/nishachar90/nifty_quant_screener.git)
cd nifty_quant_screener

###Step 3: Create & Activate a Virtual Environment
It is highly recommended to run this project inside an isolated virtual environment to keep the dependencies clean.
Bash
python3 -m venv venv
source venv/bin/activate
(Once activated, you will see (venv) at the beginning of your terminal command line).

### Step 4: Install Required Packages
Install all the necessary Python libraries (including Pandas, yfinance, Streamlit, PyArrow, and Plotly) in a single command:
Bash
pip install -r requirements.txt

### Step 5: Run the Backend Quant Pipeline
First, execute the backend engine. This script will fetch up to 10 years of historical market data, calculate the factor scores, run the portfolio simulation, and save the final CSV files and charts in the data/outputs/ folder.
Bash
python3 run_pipeline.py
(Please wait 1-2 minutes for the data ingestion and calculations to finish).

### Step 6: Launch the Interactive Dashboard
Once the backend pipeline completes successfully, start the Streamlit web application to view the stock screener, compare companies, and analyze the backtest performance:
Bash
streamlit run dashboard.py
(The dashboard will automatically open in your default web browser at http://localhost:8501).

🛑 Streamlit Configuration (Optional)
If Streamlit prompts you for an email address during the first run, you can simply press Enter to skip it.
To permanently bypass the email prompt and disable telemetry (usage data collection) on your machine, run this block of commands in your terminal:
Bash
mkdir -p .streamlit
echo '[general]' > .streamlit/config.toml
echo 'email = ""' >> .streamlit/config.toml
echo '[browser]' >> .streamlit/config.toml
echo 'gatherUsageStats = false' >> .streamlit/config.toml
