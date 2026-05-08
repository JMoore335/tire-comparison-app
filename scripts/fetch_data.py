import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from bs4 import BeautifulSoup
import time
import re
from datetime import datetime
from data.cache import init_db, insert_tire, clear_db

BASE_URL = "https://www.tyrereviews.com"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# Used to identify the test vehicle from article body text.
# Listed by region to make it easy to extend.
KNOWN_MANUFACTURERS = [
    # German
    "Volkswagen", "VW", "BMW", "Audi", "Mercedes", "Mercedes-Benz",
    "Porsche", "Opel", "Smart", "Maybach",
    # British
    "Vauxhall", "Jaguar", "Land Rover", "Range Rover", "Bentley",
    "Rolls-Royce", "Lotus", "McLaren", "Aston Martin", "MG",
    # French
    "Renault", "Peugeot", "Citroen", "Citroën", "DS", "Alpine",
    # Italian
    "Fiat", "Alfa Romeo", "Lancia", "Ferrari", "Lamborghini", "Maserati",
    # Swedish
    "Volvo", "Saab", "Polestar",
    # Czech / Spanish
    "Skoda", "Škoda", "Seat", "Cupra",
    # Japanese
    "Toyota", "Honda", "Nissan", "Mazda", "Subaru", "Mitsubishi",
    "Lexus", "Infiniti", "Suzuki", "Isuzu", "Daihatsu",
    # Korean
    "Hyundai", "Kia", "Genesis",
    # American
    "Ford", "Chevrolet", "Dodge", "Jeep", "Cadillac", "Buick",
    "Lincoln", "Chrysler", "Tesla",
    # Other
    "Mini", "MINI", "Dacia", "Lada", "Ssangyong", "SsangYong", "Lynk"
]

# Pre-built regex pattern from the manufacturer list, used in vehicle extraction
MANUFACTURER_PATTERN = "|".join(KNOWN_MANUFACTURERS)


def get_test_urls():
    """
    Scrape the TyreReviews test listing pages and return a list of
    article URLs for all own tests (test_type=tr). Covers pages 1-4.
    """
    urls = []
    for page in range(1, 5):
        url = f"{BASE_URL}/Tyre-Tests/test_type=tr/page={page}/"
        response = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        for link in soup.select("a[href*='/Tyre-Tests/']"):
            href = link.get("href", "")
            # Only keep main article links, not sub-pages or filters
            if (href
                    and ".htm" in href
                    and "test_type" not in href
                    and "page=" not in href
                    and "Results-Grid" not in href
                    and "Charts" not in href):
                full_url = BASE_URL + href if href.startswith("/") else href
                if full_url not in urls:
                    urls.append(full_url)

        time.sleep(1)

    print(f"Found {len(urls)} tests.")
    return urls


def get_article_metadata(article_url: str):
    """
    Fetch the main article page and extract the test name, year, tire size,
    and test vehicle. Uses three strategies in order of reliability:

    1. Structured metadata block — newer articles have a dedicated block
       with labelled fields like 'Test Vehicle' and 'Tyre Size'.
    2. Meta description tag — older articles often describe the test
       in the page meta description (e.g. 'using a Ford Focus RS').
    3. Body text search — scans the full article text for known
       manufacturer names as a last resort.
    """
    try:
        response = requests.get(article_url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        body_text = soup.get_text(" ", strip=True)

        # Test name from the page h1
        h1 = soup.find("h1")
        test_name = h1.get_text(strip=True) if h1 else "Unknown"

        # Extract year from test name using a 4-digit year pattern
        year_match = re.search(r'\b(20\d{2})\b', test_name)
        test_year = int(year_match.group(1)) if year_match else None

        tire_size = None
        test_vehicle = None

        # Strategy 1: structured metadata block (newer articles)
        all_text_elements = soup.find_all(string=True)
        clean = [t.strip() for t in all_text_elements if t.strip()]
        for i, text in enumerate(clean):
            if text == "Test Vehicle" and i + 1 < len(clean):
                test_vehicle = clean[i + 1]
            if text == "Tyre Size" and i + 1 < len(clean):
                tire_size = clean[i + 1]

        # Strategy 2: meta description tag (older articles)
        if not test_vehicle or not tire_size:
            meta = (soup.find("meta", {"name": "description"}) or
                    soup.find("meta", {"property": "og:description"}))
            if meta:
                desc = meta.get("content", "")
                if not tire_size:
                    size_match = re.search(r'\b(\d{3}/\d{2}\s?R\d{2})\b', desc)
                    tire_size = size_match.group(1).strip() if size_match else None
                if not test_vehicle:
                    vehicle_match = re.search(
                        r'using (?:a |an )?([A-Z][a-zA-Z\-]+(?: [A-Z][a-zA-Z\-]+){0,3})',
                        desc
                    )
                    test_vehicle = vehicle_match.group(1).strip() if vehicle_match else None

        # Strategy 3: scan body text for known manufacturer names
        if not test_vehicle:
            vehicle_match = re.search(
                rf'\b({MANUFACTURER_PATTERN})\b\s+([A-Z][a-zA-Z0-9]{{1,20}}(?:\s+[A-Z][a-zA-Z0-9]{{1,15}}){{0,2}})',
                body_text
            )
            if vehicle_match:
                test_vehicle = f"{vehicle_match.group(1)} {vehicle_match.group(2)}".strip()

        # If no size found yet, try extracting from body text
        all_sizes = list(set(re.findall(r'\b(\d{3}/\d{2}\s?R\d{2})\b', body_text)))
        if not tire_size and all_sizes:
            tire_size = all_sizes[0]

        # Flag ambiguous cases where multiple sizes or vehicles are detected
        if len(all_sizes) > 1:
            print(f"  Warning: Multiple sizes found: {all_sizes} — using: {tire_size}")

        if test_vehicle:
            all_vehicles = list(set(re.findall(
                rf'\b({MANUFACTURER_PATTERN})\b\s+[A-Z][a-zA-Z0-9]{{1,20}}',
                body_text
            )))
            if len(all_vehicles) > 1:
                print(f"  Warning: Multiple vehicles found: {all_vehicles} — using: {test_vehicle}")

        return test_name, test_year, tire_size, test_vehicle

    except Exception as e:
        print(f"  Metadata error: {e}")
        return "Unknown", None, None, None


def clean_value(text: str):
    """
    Parse a raw cell value from the results table to a float.
    TyreReviews appends ranking markers (★, 1, 2, 3) to values
    in the top positions — these are stripped before parsing.
    """
    if not text:
        return None
    text = re.sub(r'[★▼▲]', '', text)       # Remove symbol markers
    text = re.sub(r'\s+[123★]$', '', text)   # Remove trailing rank numbers
    text = re.sub(r'[^\d.\-]', '', text)     # Keep only numeric characters
    try:
        return float(text)
    except ValueError:
        return None


def extract_brand(tire_name: str):
    """
    Extract the brand name from a tire model name.
    TyreReviews formats model names as 'Brand ModelName',
    so the first word is always the brand.
    Reference tires used for calibration are excluded.
    """
    if not tire_name or "reference" in tire_name.lower():
        return None
    return tire_name.split()[0]


def build_column_map(table):
    """
    Parse the two-row header structure of a TyreReviews Results Grid table
    and return a dict mapping field names to column indices.

    The table uses a two-level header:
    - Row 1: group labels (Dry, Wet, Comfort) with colspan attributes
    - Row 2: sub-labels (Braking M, Handling s, etc.)

    Columns that span both rows (rowspan > 1) are their own header
    (e.g. rank, tire name, total score).
    """
    rows = table.find_all("tr")
    if len(rows) < 2:
        return {}

    first_row = rows[0].find_all(["th", "td"])
    second_row = rows[1].find_all(["th", "td"])

    # Expand first header row into a flat list, accounting for colspan
    col_groups = []
    col_idx = 0
    for cell in first_row:
        rowspan = int(cell.get("rowspan", 1))
        colspan = int(cell.get("colspan", 1))
        label = cell.get_text(strip=True).lower()
        for _ in range(colspan):
            col_groups.append({
                "idx": col_idx,
                "group": label,
                "own_header": rowspan > 1  # True = this cell spans both header rows
            })
            col_idx += 1

    # Fill in sub-headers from the second row for columns that need it
    sub_idx = 0
    for col in col_groups:
        if not col["own_header"]:
            if sub_idx < len(second_row):
                col["sub"] = second_row[sub_idx].get_text(strip=True).lower()
                sub_idx += 1
            else:
                col["sub"] = ""
        else:
            col["sub"] = col["group"]

    # Map combined group + sub labels to our database field names
    field_map = {}
    for col in col_groups:
        group = col.get("group", "")
        sub = col.get("sub", "")
        idx = col["idx"]

        if col["group"] in ("#", "rank", ""):
            field_map.setdefault("rank", idx)
        elif "tyre" in sub or "tyre" in group or col["idx"] == 1:
            field_map.setdefault("name", idx)
        elif "total" in sub or "total" in group:
            field_map.setdefault("overall_score", idx)
        elif "dry" in group and "brak" in sub:
            field_map.setdefault("dry_braking", idx)
        elif "dry" in group and "handl" in sub and "subj" not in sub:
            field_map.setdefault("dry_handling", idx)
        elif "dry" in group and "subj" in sub:
            field_map.setdefault("subj_dry_handling", idx)
        elif "wet" in group and "brak" in sub:
            field_map.setdefault("wet_braking", idx)
        elif "wet" in group and "handl" in sub and "subj" not in sub:
            field_map.setdefault("wet_handling", idx)
        elif "wet" in group and "subj" in sub:
            field_map.setdefault("subj_wet_handling", idx)
        elif "straight" in sub or ("aqua" in sub and "straight" in sub):
            field_map.setdefault("straight_aquaplaning", idx)
        elif "curved" in sub:
            field_map.setdefault("curved_aquaplaning", idx)
        elif "noise" in sub:
            field_map.setdefault("noise_db", idx)
        elif "comfort" in sub and "subj" in sub:
            field_map.setdefault("subj_comfort", idx)
        elif "rolling" in sub or "resistance" in sub:
            field_map.setdefault("rolling_resistance", idx)

    return field_map


def parse_results_grid(grid_url: str, test_name: str, test_year: int,
                       tire_size: str, test_vehicle: str):
    """
    Fetch and parse a Results Grid page for a single test.
    Finds the largest table on the page (the results table),
    maps its columns using build_column_map, then extracts one
    record per tire row and returns them as a list of dicts.
    """
    try:
        response = requests.get(grid_url, headers=HEADERS, timeout=10)
        if response.status_code != 200:
            print(f"  HTTP {response.status_code} — skipping")
            return []
        soup = BeautifulSoup(response.text, "html.parser")
    except Exception as e:
        print(f"  Fetch error: {e}")
        return []

    # Pick the table with the most data cells — that's always the results table
    tables = soup.find_all("table")
    if not tables:
        print("  No table found")
        return []
    table = max(tables, key=lambda t: len(t.find_all("td")))

    col_map = build_column_map(table)
    if not col_map:
        print("  Could not parse headers")
        return []

    results = []
    data_rows = [r for r in table.find_all("tr") if r.find("td")]

    for row in data_rows:
        cells = row.find_all(["td", "th"])
        if len(cells) < 3:
            continue

        def cell_text(field):
            """Helper to safely get text from a cell by field name."""
            idx = col_map.get(field)
            if idx is not None and idx < len(cells):
                return cells[idx].get_text(strip=True)
            return ""

        # Tire name is in a linked cell — prefer the anchor text
        name_idx = col_map.get("name", 1)
        name_cell = cells[name_idx] if name_idx < len(cells) else None
        if not name_cell:
            continue
        link = name_cell.find("a")
        tire_name = link.get_text(strip=True) if link else name_cell.get_text(strip=True)

        if not tire_name or "reference" in tire_name.lower():
            continue

        brand = extract_brand(tire_name)
        if not brand:
            continue

        # Extract TyreReviews' own rank from the first column
        rank_text = cell_text("rank")
        rank_match = re.search(r'\d+', rank_text)
        overall_rank = int(rank_match.group()) if rank_match else None

        tire_data = {
            "test_name":           test_name,
            "test_url":            grid_url,
            "test_year":           test_year,
            "tire_size":           tire_size,
            "test_vehicle":        test_vehicle,
            "brand":               brand,
            "model":               tire_name,
            "wet_braking":         clean_value(cell_text("wet_braking")),
            "dry_braking":         clean_value(cell_text("dry_braking")),
            "wet_handling":        clean_value(cell_text("wet_handling")),
            "dry_handling":        clean_value(cell_text("dry_handling")),
            "subj_wet_handling":   clean_value(cell_text("subj_wet_handling")),
            "subj_dry_handling":   clean_value(cell_text("subj_dry_handling")),
            "straight_aquaplaning":clean_value(cell_text("straight_aquaplaning")),
            "curved_aquaplaning":  clean_value(cell_text("curved_aquaplaning")),
            "noise_db":            clean_value(cell_text("noise_db")),
            "subj_comfort":        clean_value(cell_text("subj_comfort")),
            "overall_rank":        overall_rank,
            "overall_score":       clean_value(cell_text("overall_score")),
            "scraped_at":          datetime.now().isoformat(),
        }

        results.append(tire_data)

    return results


def scrape_all():
    """
    Main entry point. Orchestrates the full scrape:
    1. Initialise and clear the database
    2. Collect all test article URLs from TyreReviews
    3. For each test, fetch metadata from the article page
    4. Fetch and parse the Results Grid page
    5. Insert each tire record into the database

    Includes polite delays between requests to avoid overloading the server.
    """
    print("Initialising database...")
    init_db()
    clear_db()

    print("Fetching test URLs...")
    test_urls = get_test_urls()

    total_saved = 0

    for i, article_url in enumerate(test_urls):
        print(f"\n[{i+1}/{len(test_urls)}] {article_url}")

        test_name, test_year, tire_size, test_vehicle = get_article_metadata(article_url)
        print(f"  Name:    {test_name}")
        print(f"  Year:    {test_year}")
        print(f"  Size:    {tire_size}")
        print(f"  Vehicle: {test_vehicle}")

        grid_url = article_url.rstrip("/") + "/Results-Grid/"
        print(f"  Grid:    {grid_url}")
        time.sleep(1)

        results = parse_results_grid(grid_url, test_name, test_year, tire_size, test_vehicle)
        for tire in results:
            insert_tire(tire)
            total_saved += 1

        print(f"  Saved:   {len(results)} tires")
        time.sleep(1.5)  # Polite delay between requests

    print(f"\nDone. Total tire records saved: {total_saved}")


if __name__ == "__main__":
    scrape_all()