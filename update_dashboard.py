"""
Script to update the dashboard HTML with new venture‑deal data from a CSV file.

This tool reads a CSV file containing the venture capital deals, converts it
into an array of dictionaries (matching the keys used in the dashboard),
and then replaces the existing data array in `dashboard.html` with the
freshly serialised JSON. The updated file is written to `dashboard_updated.html`.

Usage:
    python update_dashboard.py --csv path/to/deals.csv --html path/to/dashboard.html

If no arguments are provided, the script defaults to:
    CSV:  vc_deals_jul29_2025.csv
    HTML: dashboard.html

After running the script, replace the old HTML with the new file or host it
via a static server as described in the README. You can schedule this
script (e.g. via cron or a GitHub Action) to automate daily updates.
"""

import argparse
import csv
import json
import re
from pathlib import Path


def parse_csv(csv_path: Path) -> list:
    """Read a CSV of deals and return a list of dicts with expected keys."""
    deals = []
    with csv_path.open(newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Normalise keys to match those used in the dashboard
            deal = {
                'Company': row.get('Company'),
                'Date': row.get('Date'),
                'Time': row.get('Time') or '',
                'Location': row.get('Location'),
                'Industry': row.get('Industry') or '',
                'Round': row.get('Round'),
                'Amount ($M)': float(row['Amount ($M)']) if row.get('Amount ($M)') else None,
                'Lead Investor': row.get('Lead Investor'),
                'Other Investors': row.get('Other Investors'),
                'Description': row.get('Description'),
            }
            deals.append(deal)
    return deals


def update_dashboard(html_path: Path, data: list) -> None:
    """Replace the data array in the dashboard with the provided data."""
    html_text = html_path.read_text(encoding='utf-8')

    # Assign a timestamp (HH:MM) to all deals representing when this update is run.
    try:
        from datetime import datetime
        # Try to convert to America/Los_Angeles; fallback to local time if zoneinfo isn't available
        try:
            from zoneinfo import ZoneInfo
            update_time = datetime.now(tz=ZoneInfo('America/Los_Angeles')).strftime('%H:%M')
        except Exception:
            update_time = datetime.now().strftime('%H:%M')
        for row in data:
            # Only set Time if it's missing or blank
            if not row.get('Time'):
                row['Time'] = update_time
    except Exception:
        pass
    json_str = json.dumps(data, indent=2, ensure_ascii=False)
    # Replace the data array in the script section
    pattern = r"const data = \[[\s\S]*?\];"
    replacement = f"const data = {json_str};"
    updated = re.sub(pattern, replacement, html_text, flags=re.MULTILINE)

    # Update the date shown in the H1 heading based on the most recent deal date
    try:
        # Extract the latest date string (YYYY-MM-DD) from the data
        dates = [row['Date'] for row in data if row.get('Date')]
        latest = max(dates)
        from datetime import datetime
        dt = datetime.strptime(latest, '%Y-%m-%d')
        # Format with non‑breaking spaces so the date doesn't wrap
        formatted_date = dt.strftime('%B\u00a0%d\u00a0%Y')
        h1_pattern = r"(Meera's Daily Tech VC Deals \()([^)]*)(\))"
        updated = re.sub(h1_pattern, lambda m: m.group(1) + formatted_date + m.group(3), updated)
    except Exception as exc:
        # If anything goes wrong, leave the existing date in place
        pass

    output_path = html_path.with_name('dashboard_updated.html')
    output_path.write_text(updated, encoding='utf-8')
    print(f"Updated dashboard written to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Update dashboard data from CSV")
    parser.add_argument('--csv', type=Path, default=Path('vc_deals_jul29_2025.csv'), help='Path to CSV file with deal data')
    parser.add_argument('--html', type=Path, default=Path('dashboard.html'), help='Path to the existing dashboard HTML file')
    args = parser.parse_args()
    data = parse_csv(args.csv)
    update_dashboard(args.html, data)


if __name__ == '__main__':
    main()
