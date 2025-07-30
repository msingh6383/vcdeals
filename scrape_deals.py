"""
Scrape the most recent venture capital deals from VC News Daily.

This script pulls the 'Recent Venture Capital Financings' from the VC News
Daily front page, visits each individual article, and extracts key
information such as company name, funding amount, round, date, lead
investor(s) and other investors. It writes the results to a CSV file.

Note: This is a basic scraper intended as a starting point. VC News Daily
doesn't provide a formal API, so the structure of pages may change and
parse logic may need adjustments over time. Always abide by the site's
terms of use and robots.txt when scraping.

Example usage:
    python scrape_deals.py --output vc_deals.csv

"""

import argparse
import csv
import re
from datetime import datetime
from urllib.parse import unquote

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://vcnewsdaily.com"


def extract_deal_info(article_url: str) -> dict:
    """Extract deal information from a VC News Daily article page."""
    resp = requests.get(article_url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')

    # Title typically contains company and deal summary
    h2 = soup.find('h2')
    title = h2.get_text(strip=True) if h2 else ''

    # Extract date (formatted YYYY-MM-DD) – find the first text matching date pattern
    date_match = soup.find(string=re.compile(r"^\d{4}-\d{2}-\d{2}"))
    date = date_match.strip() if date_match else ''

    # Extract location and description from the first paragraph (if available)
    paragraphs = soup.find_all('p')
    location = ''
    description = ''
    if paragraphs:
        # The first paragraph usually contains location and a short description
        first_p = paragraphs[0].get_text(separator=' ', strip=True)
        # Location appears before the first comma
        parts = first_p.split(',')
        if len(parts) > 1:
            location = parts[0].strip()
            description = ','.join(parts[1:]).strip()
        else:
            description = first_p

    # Extract amount and round from the title using regex
    amount_m = None
    round_type = ''
    amount_match = re.search(r"\$(\d+[\.\d]*)\s*([MB])?\s*(?:in\s*)?([A-Za-z0-9\+ &]*?)\s*Round", title, re.IGNORECASE)
    if amount_match:
        amount_val = float(amount_match.group(1))
        scale = amount_match.group(2)
        round_type = amount_match.group(3).strip()
        # Convert to millions for consistency
        if scale and scale.upper() == 'B':
            amount_m = amount_val * 1000
        else:
            amount_m = amount_val

    # Company name: take the part of the title before the first verb (e.g. 'Grabs', 'Announces', 'Scores')
    company = title
    verbs = ['Grabs', 'Announces', 'Closes', 'Extends', 'Snares', 'Inks', 'Scores', 'Scoops', 'Lands', 'Secures', 'Completes', 'Pulls', 'Bags', 'Receives', 'Launches', 'Inks']
    for verb in verbs:
        if verb in title:
            company = title.split(verb)[0].strip()
            break

    # Lead investor and other investors
    # Search for a sentence containing 'led by' and 'participation'
    page_text = soup.get_text(separator=' ', strip=True)
    lead_investor = ''
    other_investors = ''
    lead_match = re.search(r'led by ([^.,;]+)', page_text, re.IGNORECASE)
    if lead_match:
        lead_investor = lead_match.group(1).strip()
    others_match = re.search(r'participation (?:from|by) ([^.,;]+)', page_text, re.IGNORECASE)
    if others_match:
        other_investors = others_match.group(1).strip()

    return {
        'Company': unquote(company),
        'Date': date,
        'Location': location,
        'Round': round_type if round_type else '',
        'Amount ($M)': amount_m if amount_m is not None else '',
        'Lead Investor': lead_investor,
        'Other Investors': other_investors,
        'Description': description,
    }


def scrape_recent_deals(limit: int = None) -> list:
    """Scrape the recent venture capital financings from the VC News Daily homepage.

    Args:
        limit: Optional maximum number of deals to scrape. If None, scrape all found.

    Returns:
        A list of deal dictionaries.
    """
    resp = requests.get(BASE_URL)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')

    # Collect article links that include '/venture-capital-funding/'
    links = []
    for a in soup.find_all('a', href=True):
        href = a['href']
        if '/venture-capital-funding/' in href:
            # Exclude the generic venturetrackr link
            if 'venturetrackr.php' in href:
                continue
            links.append(href)

    # Deduplicate while preserving order
    seen = set()
    unique_links = []
    for link in links:
        if link not in seen:
            unique_links.append(link)
            seen.add(link)
        if limit and len(unique_links) >= limit:
            break

    deals = []
    for link in unique_links:
        # Ensure absolute URL
        if not link.startswith('http'):
            article_url = BASE_URL.rstrip('/') + '/' + link.lstrip('/')
        else:
            article_url = link
        try:
            deal = extract_deal_info(article_url)
            deals.append(deal)
        except Exception as e:
            print(f"Failed to parse {article_url}: {e}")
    return deals


def write_csv(deals: list, output_path: str) -> None:
    """Write list of deals to a CSV file."""
    if not deals:
        print("No deals scraped.")
        return
    fieldnames = list(deals[0].keys())
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for deal in deals:
            writer.writerow(deal)
    print(f"Wrote {len(deals)} deals to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Scrape recent venture deals from VC News Daily")
    parser.add_argument('--limit', type=int, default=None, help='Maximum number of deals to scrape')
    parser.add_argument('--output', type=str, default='vc_deals.csv', help='Output CSV file')
    args = parser.parse_args()
    deals = scrape_recent_deals(limit=args.limit)
    write_csv(deals, args.output)


if __name__ == '__main__':
    main()
