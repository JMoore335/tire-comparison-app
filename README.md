## Tire Performance Metric Comparison App
James Moore
jamesmoore197@gmail.com

## Purpose
    This tire performance metric comparison app allows the user to select between a list of tire models and it compares their performance differences. 

    Performance Metrics - 
        Dry Braking (m) - Distance to stop from 100 km/h on a dry surface. Lower is better.
        Dry Handling (s) - Lap time on a dry handling circuit. Lower is better.
        Wet Braking (m) - Distance to stop from 80 km/h on a wet surface. Lower is better.
        Wet Handling (s) - Lap time on a wet handling circuit. Lower is better.
        Aquaplaning (km/h) - Speed at which the tire begins to lose contact with a wet surface. Higher is better.

    Test Repeatability - 
        Tire comparison cohorts must share the same tire size and must have been tested on the same vehicle. Cohort-to-cohort comparisons can be made be using the relative score % from it's own test.

## Data Sources 
    67 tire tests were scraped from tyrereviews.com. (Example test: https://www.tyrereviews.com/Tyre-Tests/2019-Tire-Reviews-UHP-Summer-Tyre-Test.htm).
    The authors seem to have gone to great lengths to making the tests repeatable and removing chances of errors. Link to their full testing methodology and equipment used: https://www.tyrereviews.com/Article/Testing-Methodology.htm.

## Limitations & Assumptions
    A lack of tire tests which used the exact same tire size, same vehicle, and same road conditions was the largest limitation that I encountered. Also, publications use a variety of performance metrics, so I decided to use one single data source to keep the metrics uniform.

    The assumption is that the data source (Tyrereviews.com) has no financial or other incentives which could create a bias in their data.

## Potential Improvements 
    More data sources.
    A larger or more specific set of performance metrics.
    Lots of room for improvement on the app, such as better filtering, filtering by vehicle model, filter by tire season type (i.e. Winter/Summer/Competition).
    The app has little error handling.
    The data scraping still has a few parameters that weren't being picked up.


## Setup and Installation 
    Requirements: Python 3.12, Git
    
    1. Clone the repository
        bashgit clone https://github.com/JMoore335/tire-comparison-app.git
        cd tire-comparison-app
    
    2. Create and activate a virtual environment
        bashpython -m venv venv
        # Windows
            venv\Scripts\activate
        # Mac / Linux
            source venv/bin/activate
    
    3. Install dependencies
        bashpip install -r requirements.txt
    
    4. Add your API key
        Copy .env.example to .env and add your OpenAI API key:
            OPENAI_API_KEY=your_key_here
    
    5. Fetch the data
        This scrapes TyreReviews and populates the local database. Only needs to be run once (I have included the db just for the purpose of this assessment, but the scraper works).
            bashpython scripts/fetch_data.py
    
    6. Run the app
        bashstreamlit run app.py
        The app will open at http://localhost:8501.


## Tech Stack
    | Tool | Purpose | Why it was chosen |

    | **Streamlit** | User interface | Allows a fully interactive web UI to be built entirely in Python, with no frontend development required |

    | **LangGraph** | Agent orchestration | Provides a structured, extensible workflow for chaining LLM calls and data steps — easy to expand with additional nodes in future |

    | **OpenAI GPT-4o** | AI analysis | Reads structured test data and produces a written performance summary, grounding its analysis in real measured figures |

    | **Requests + BeautifulSoup** | Web scraping | Lightweight and reliable for targeting the specific HTML structure of TyreReviews results pages |

    | **SQLite** | Local data storage | Zero-configuration database built into Python, sufficient for this dataset size and straightforward to query |

    | **Pandas** | Data manipulation | Industry standard for tabular data in Python — used for cleaning, ranking, and computing relative performance metrics |

    | **Plotly** | Visualisation | Interactive charts with minimal code; horizontal bar charts and heatmaps render well inside Streamlit |

    | **Python-dotenv** | API key management | Keeps credentials out of the codebase via a local `.env` file |




## Project Structure

    ```
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
    ```




