ANALYSIS_PROMPT = """You are an expert tire analyst. You have been given real professional test data from TyreReviews for {tire_size} tyres. The data comes from controlled, instrumented tests — not user opinions.

Here is the test data:
{tire_data}

Please provide:

1. **Overall Summary** (2-3 sentences): How do these four brands compare at a high level?

2. **Best for Wet Weather**: Which tyre performs best in wet conditions (wet braking distance, wet handling, aquaplaning) and why?

3. **Best for Dry Performance**: Which tyre performs best in dry conditions and why?

4. **Best for Comfort & Noise**: Which tyre is quietest and most comfortable?

5. **Overall Recommendation**: If you had to pick one tyre, which would it be and why?

Important rules:
- Only reference metrics that are actually present in the data — do not invent figures
- For braking distances, lower is better
- For handling lap times, lower is better
- For aquaplaning speeds, higher is better
- Be specific — reference actual numbers where possible
- If data is sparse or missing for some brands, acknowledge that honestly
"""