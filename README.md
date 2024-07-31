🌟 MonitoringScrapingTool 🌟

🎩✨ This Python-based monitoring tool is designed to scrape price and seller details from e-commerce website https://www.exito.com/. Whether you are focused on Exito or any other target website, this tool gathers product data every 30 minutes from Monday to Saturday, from 9 AM to 6 PM and updates the product data into a Google Sheets. Think of it as a virtual market researcher helping sellers stay competitive by keeping a sharp eye on pricing and seller details across the web! 🚀🛒


📜 Table of Contents

1. Features
2. Installation
3. Usage


🔧 Features

- Scheduled Monitoring: runs Monday to Saturday every 30 minutes from 9 AM to 6 PM.
- Easy Deployment: deployed using a crontab job on an Ubuntu VPS.
- Logging: logs everything it monitors for easy review and analysis.


🛠️ Installation

Follow these simple steps to get MonitoringScrapingTool up and running:

1. Clone the Repository:

   git clone https://github.com/dsprovider/exito_web_scraper_monitoring.git
   cd exito_web_scraper_monitoring

3. Install Dependencies:
   Make sure you have Python 3.11.1 or higher. Install the necessary packages using pip:
   pip install -r requirements.txt

5. Set Up Crontab:
   To ensure MonitoringScrapingTool runs on schedule, access your VPS and set up a crontab job. Start by opening your crontab configuration:
   crontab -e

   Add the following line to run the script every 30 minutes during the active monitoring hours. You can adjust the interval as needed, but make sure to avoid overlapping job executions:
   */30 9-18 * * 1-6 /usr/bin/python3 /home/exito_web_scraper_monitoring/exito_web_scraper_monitoring/exitoScraper_20240629A.py


⚙️ Usage

To manually run the script for testing:
python3 exitoScraper_20240629A.py

Once you have configured the crontab job, your setup should be good to go. To ensure the cron job is running as expected, restart or reload the cron service and check its status:
service cron restart
service cron status
