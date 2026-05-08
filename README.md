# Tire Performance Comparison App

James Moore

## Purpose

This tire performance metric comparison app allows the user to select between a list of tire models and compare their performance across professional instrumented tests.

**Performance Metrics**

| Metric | Description | Direction |
|---|---|---|
| Dry Braking (m) | Distance to stop from 100 km/h on a dry surface | Lower is better |
| Dry Handling (s) | Lap time on a dry handling circuit | Lower is better |
| Wet Braking (m) | Distance to stop from 80 km/h on a wet surface | Lower is better |
| Wet Handling (s) | Lap time on a wet handling circuit | Lower is better |
| Aquaplaning (km/h) | Speed at which the tire begins to lose contact with a wet surface | Higher is better |

**Test Repeatability**

Tire comparison cohorts must share the same tire size and must have been tested on the same vehicle. Cross-cohort comparisons can be made using the Relative Score (%).

**Relative Score (%)** — An aggregate score calculated by expressing each tire's performance as a percentage of the best performer in that metric across each test. Each of the five metrics is weighted equally. A score of 100% means the tire was the best in that metric; lower scores indicate how far behind the best performer the tire was.

---

## Data Source

67 tire tests were scraped from [TyreReviews](https://www.tyrereviews.com). The authors conduct fully instrumented, repeatable tests on professional proving grounds. Their full testing methodology and equipment details can be found [here](https://www.tyrereviews.com/Article/Testing-Methodology.htm).

---

## Limitations and Assumptions

- The largest limitation was the lack of tests using the exact same tire size, vehicle, and road conditions, limiting the number of valid direct comparisons.
- A single data source was used deliberately to keep performance metrics uniform across all tests.
- The assumption is made that TyreReviews has no financial or other incentive that could introduce bias into their results.

---

## Potential Improvements

- Additional data sources to increase test coverage
- A larger or more specific set of performance metrics
- Better filtering — by vehicle model, tire season type (Winter / Summer / Competition / All Season)
- Improved error handling throughout the application
- Some vehicle metadata was not successfully extracted during scraping and required exclusion
- Could use containerization

---

## Setup and Installation

**Requirements:** Python 3.12, Git

**1. Clone the repository**

```bash
git clone https://github.com/JMoore335/tire-comparison-app.git
cd tire-comparison-app
```

**2. Create and activate a virtual environment**

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac / Linux
source venv/bin/activate
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Add your API key**

Copy `.env.example` to `.env` and add your OpenAI API key:
OPENAI_API_KEY=your_key_here

**5. Fetch the data**

This scrapes TyreReviews and populates the local database. Only needs to be run once. A pre-populated database is included in the repository for convenience.

```bash
python scripts/fetch_data.py
```

**6. Run the app**

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`.

---

## Tech Stack

| Tool | Purpose | Why it was chosen |
|---|---|---|
| **Streamlit** | User interface | Allows a fully interactive web UI to be built entirely in Python, with no frontend development required |
| **LangGraph** | Agent orchestration | Provides a structured, extensible workflow for chaining LLM calls and data steps — easy to expand with additional nodes in future |
| **OpenAI GPT-4o** | AI analysis | Reads structured test data and produces a written performance summary, grounding its analysis in real measured figures |
| **Requests + BeautifulSoup** | Web scraping | Lightweight and reliable for targeting the specific HTML structure of TyreReviews results pages |
| **SQLite** | Local data storage | Zero-configuration database built into Python, sufficient for this dataset size and straightforward to query |
| **Pandas** | Data manipulation | Industry standard for tabular data in Python — used for cleaning, ranking, and computing relative performance metrics |
| **Plotly** | Visualisation | Interactive charts with minimal code; horizontal bar charts render well inside Streamlit |
| **Python-dotenv** | API key management | Keeps credentials out of the codebase via a local `.env` file |

---

## Project Structure

tire-comparison-app/
├── app.py                  # Streamlit UI and visualisation logic
├── agent/
│   ├── graph.py            # LangGraph workflow
│   ├── tools.py            # LLM analysis functions
│   └── prompts.py          # LLM prompts
├── data/
│   └── cache.py            # SQLite database layer
├── scripts/
│   └── fetch_data.py       # TyreReviews scraper
├── requirements.txt
├── .env.example
└── README.md