name: Update VC dashboard

on:
  schedule:
    - cron:  '0 1 * * *'  # runs at 01:00 UTC every day
  workflow_dispatch:      # allows you to run it manually from the Actions tab

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install requests beautifulsoup4

      - name: Run scraper and update dashboard
        run: |
          python scrape_deals.py              # this creates or updates vc_deals.csv
          python update_dashboard.py --csv vc_deals.csv --html dashboard.html

      - name: Commit and push changes
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add .
          git commit -m "Automated daily update" || echo "No changes to commit"
          git push
