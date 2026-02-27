"""
Teleport API integration — global city cost of living + housing data
====================================================================
Free API, no auth required. Covers 200+ cities worldwide.
Base: https://api.teleport.org/api/

Routing rule:
  Austin TX area queries → use real_estate.py (ACTRIS MLS data)
  All other cities worldwide → this module

Two public functions registered as agent tools:
  search_city_slug(city_name)        — find Teleport slug for a city
  get_city_housing_data(city_name)   — full housing + COL data for any city

Fallback: if Teleport API is unreachable, returns HARDCODED_FALLBACK data
for 15 major cities. Never crashes — always returns something useful.
"""

import asyncio
import httpx
from typing import Optional

# ---------------------------------------------------------------------------
# Austin TX area keywords — route these to real_estate.py, not Teleport
# ---------------------------------------------------------------------------

AUSTIN_TX_KEYWORDS = {
    "austin", "travis", "travis county", "williamson", "williamson county",
    "round rock", "cedar park", "georgetown", "leander",
    "hays", "hays county", "kyle", "buda", "san marcos", "wimberley",
    "bastrop", "bastrop county", "elgin", "smithville",
    "caldwell", "caldwell county", "lockhart", "luling",
    "austin msa", "austin metro", "greater austin", "austin-round rock",
}


def _is_austin_area(city_name: str) -> bool:
    """Returns True if the city name refers to the Austin TX ACTRIS coverage area."""
    lower = city_name.lower().strip()
    return any(kw in lower for kw in AUSTIN_TX_KEYWORDS)


# ---------------------------------------------------------------------------
# In-memory slug cache (avoids repeat search API calls)
# ---------------------------------------------------------------------------

_slug_cache: dict[str, str] = {
    "seattle": "seattle",
    "san francisco": "san-francisco-bay-area",
    "sf": "san-francisco-bay-area",
    "new york": "new-york",
    "nyc": "new-york",
    "new york city": "new-york",
    "london": "london",
    "tokyo": "tokyo",
    "sydney": "sydney",
    "toronto": "toronto",
    "berlin": "berlin",
    "paris": "paris",
    "chicago": "chicago",
    "denver": "denver",
    "miami": "miami",
    "boston": "boston",
    "los angeles": "los-angeles",
    "la": "los-angeles",
    "nashville": "nashville",
    "dallas": "dallas",
    "houston": "houston",
    "phoenix": "phoenix",
    "portland": "portland-or",
    "minneapolis": "minneapolis-st-paul",
    "atlanta": "atlanta",
    "san diego": "san-diego",
    "amsterdam": "amsterdam",
    "barcelona": "barcelona",
    "madrid": "madrid",
    "rome": "rome",
    "milan": "milan",
    "munich": "munich",
    "zurich": "zurich",
    "singapore": "singapore",
    "hong kong": "hong-kong",
    "dubai": "dubai",
    "stockholm": "stockholm",
    "oslo": "oslo",
    "copenhagen": "copenhagen",
    "vienna": "vienna",
    "brussels": "brussels",
    "montreal": "montreal",
    "vancouver": "vancouver",
    "melbourne": "melbourne",
    "auckland": "auckland",
    "mexico city": "mexico-city",
    "sao paulo": "sao-paulo",
    "buenos aires": "buenos-aires",
    "bangalore": "bangalore",
    "mumbai": "mumbai",
    "delhi": "delhi",
    "shanghai": "shanghai",
    "beijing": "beijing",
    "seoul": "seoul",
    "taipei": "taipei",
    "kuala lumpur": "kuala-lumpur",
    "jakarta": "jakarta",
    "bangkok": "bangkok",
    "cairo": "cairo",
    "cape town": "cape-town",
    "tel aviv": "tel-aviv",
}

# ---------------------------------------------------------------------------
# Hardcoded fallback — used only if Teleport API is unreachable
# ---------------------------------------------------------------------------

HARDCODED_FALLBACK: dict[str, dict] = {
    "san-francisco-bay-area": {
        "city": "San Francisco, CA",
        "ListPrice": 1_350_000, "median_price": 1_350_000,
        "MedianRentMonthly": 3200, "AffordabilityScore": 2.1,
        "col_index": 178.1, "data_source": "Fallback data (Teleport API unavailable)",
    },
    "seattle": {
        "city": "Seattle, WA",
        "ListPrice": 850_000, "median_price": 850_000,
        "MedianRentMonthly": 2400, "AffordabilityScore": 4.2,
        "col_index": 150.2, "data_source": "Fallback data (Teleport API unavailable)",
    },
    "new-york": {
        "city": "New York, NY",
        "ListPrice": 750_000, "median_price": 750_000,
        "MedianRentMonthly": 3800, "AffordabilityScore": 2.8,
        "col_index": 187.2, "data_source": "Fallback data (Teleport API unavailable)",
    },
    "denver": {
        "city": "Denver, CO",
        "ListPrice": 565_000, "median_price": 565_000,
        "MedianRentMonthly": 1900, "AffordabilityScore": 5.9,
        "col_index": 110.3, "data_source": "Fallback data (Teleport API unavailable)",
    },
    "chicago": {
        "city": "Chicago, IL",
        "ListPrice": 380_000, "median_price": 380_000,
        "MedianRentMonthly": 1850, "AffordabilityScore": 6.1,
        "col_index": 107.1, "data_source": "Fallback data (Teleport API unavailable)",
    },
    "london": {
        "city": "London, UK",
        "ListPrice": 720_000, "median_price": 720_000,
        "MedianRentMonthly": 2800, "AffordabilityScore": 3.4,
        "col_index": 155.0, "data_source": "Fallback data (Teleport API unavailable)",
    },
    "toronto": {
        "city": "Toronto, Canada",
        "ListPrice": 980_000, "median_price": 980_000,
        "MedianRentMonthly": 2300, "AffordabilityScore": 3.8,
        "col_index": 132.0, "data_source": "Fallback data (Teleport API unavailable)",
    },
    "sydney": {
        "city": "Sydney, Australia",
        "ListPrice": 1_100_000, "median_price": 1_100_000,
        "MedianRentMonthly": 2600, "AffordabilityScore": 3.2,
        "col_index": 148.0, "data_source": "Fallback data (Teleport API unavailable)",
    },
    "berlin": {
        "city": "Berlin, Germany",
        "ListPrice": 520_000, "median_price": 520_000,
        "MedianRentMonthly": 1600, "AffordabilityScore": 6.2,
        "col_index": 95.0, "data_source": "Fallback data (Teleport API unavailable)",
    },
    "tokyo": {
        "city": "Tokyo, Japan",
        "ListPrice": 650_000, "median_price": 650_000,
        "MedianRentMonthly": 1800, "AffordabilityScore": 5.1,
        "col_index": 118.0, "data_source": "Fallback data (Teleport API unavailable)",
    },
    "miami": {
        "city": "Miami, FL",
        "ListPrice": 620_000, "median_price": 620_000,
        "MedianRentMonthly": 2800, "AffordabilityScore": 4.1,
        "col_index": 123.4, "data_source": "Fallback data (Teleport API unavailable)",
    },
    "boston": {
        "city": "Boston, MA",
        "ListPrice": 720_000, "median_price": 720_000,
        "MedianRentMonthly": 3100, "AffordabilityScore": 3.9,
        "col_index": 162.3, "data_source": "Fallback data (Teleport API unavailable)",
    },
    "nashville": {
        "city": "Nashville, TN",
        "ListPrice": 450_000, "median_price": 450_000,
        "MedianRentMonthly": 1800, "AffordabilityScore": 6.4,
        "col_index": 96.8, "data_source": "Fallback data (Teleport API unavailable)",
    },
    "dallas": {
        "city": "Dallas, TX",
        "ListPrice": 380_000, "median_price": 380_000,
        "MedianRentMonthly": 1700, "AffordabilityScore": 6.8,
        "col_index": 96.2, "data_source": "Fallback data (Teleport API unavailable)",
    },
    "los-angeles": {
        "city": "Los Angeles, CA",
        "ListPrice": 950_000, "median_price": 950_000,
        "MedianRentMonthly": 2900, "AffordabilityScore": 3.0,
        "col_index": 165.0, "data_source": "Fallback data (Teleport API unavailable)",
    },
    "paris": {
        "city": "Paris, France",
        "ListPrice": 850_000, "median_price": 850_000,
        "MedianRentMonthly": 2200, "AffordabilityScore": 3.6,
        "col_index": 138.0, "data_source": "Fallback data (Teleport API unavailable)",
    },
    "amsterdam": {
        "city": "Amsterdam, Netherlands",
        "ListPrice": 680_000, "median_price": 680_000,
        "MedianRentMonthly": 2100, "AffordabilityScore": 4.0,
        "col_index": 128.0, "data_source": "Fallback data (Teleport API unavailable)",
    },
    "singapore": {
        "city": "Singapore",
        "ListPrice": 1_200_000, "median_price": 1_200_000,
        "MedianRentMonthly": 2800, "AffordabilityScore": 3.0,
        "col_index": 145.0, "data_source": "Fallback data (Teleport API unavailable)",
    },
    "hong-kong": {
        "city": "Hong Kong",
        "ListPrice": 1_500_000, "median_price": 1_500_000,
        "MedianRentMonthly": 3500, "AffordabilityScore": 1.8,
        "col_index": 185.0, "data_source": "Fallback data (Teleport API unavailable)",
    },
    "zurich": {
        "city": "Zurich, Switzerland",
        "ListPrice": 1_100_000, "median_price": 1_100_000,
        "MedianRentMonthly": 3000, "AffordabilityScore": 2.9,
        "col_index": 175.0, "data_source": "Fallback data (Teleport API unavailable)",
    },
    "vancouver": {
        "city": "Vancouver, Canada",
        "ListPrice": 1_050_000, "median_price": 1_050_000,
        "MedianRentMonthly": 2500, "AffordabilityScore": 3.1,
        "col_index": 142.0, "data_source": "Fallback data (Teleport API unavailable)",
    },
    "seoul": {
        "city": "Seoul, South Korea",
        "ListPrice": 700_000, "median_price": 700_000,
        "MedianRentMonthly": 1600, "AffordabilityScore": 4.5,
        "col_index": 108.0, "data_source": "Fallback data (Teleport API unavailable)",
    },
    "dubai": {
        "city": "Dubai, UAE",
        "ListPrice": 800_000, "median_price": 800_000,
        "MedianRentMonthly": 2400, "AffordabilityScore": 4.0,
        "col_index": 120.0, "data_source": "Fallback data (Teleport API unavailable)",
    },
}

_TELEPORT_BASE = "https://api.teleport.org/api"
_REQUEST_TIMEOUT = 8.0  # seconds


# ---------------------------------------------------------------------------
# Slug resolution
# ---------------------------------------------------------------------------

async def search_city_slug(city_name: str) -> Optional[str]:
    """
    Finds the Teleport urban area slug for a city name.

    Strategy:
      1. Exact match in local _slug_cache (instant, no API call)
      2. Call Teleport city search API and extract urban_area slug
      3. Cache result for future calls
      4. Return None if not found

    Args:
        city_name: Human-readable city name (e.g. "Seattle", "San Francisco")

    Returns:
        Teleport slug string (e.g. "seattle") or None if not found.
    """
    lower = city_name.lower().strip()

    if lower in _slug_cache:
        return _slug_cache[lower]

    try:
        async with httpx.AsyncClient(timeout=_REQUEST_TIMEOUT) as client:
            resp = await client.get(
                f"{_TELEPORT_BASE}/cities/",
                params={
                    "search": city_name,
                    "embed": "city:search-results/city:item/city:urban_area",
                },
            )
            resp.raise_for_status()
            data = resp.json()

        results = (
            data.get("_embedded", {})
            .get("city:search-results", [])
        )
        for item in results:
            city_item = item.get("_embedded", {}).get("city:item", {})
            urban_area_links = city_item.get("_links", {}).get("city:urban_area", {})
            ua_href = urban_area_links.get("href", "")
            if "urban_areas/slug:" in ua_href:
                slug = ua_href.split("slug:")[-1].rstrip("/")
                _slug_cache[lower] = slug
                return slug

    except Exception:
        pass

    return None


# ---------------------------------------------------------------------------
# Main data function
# ---------------------------------------------------------------------------

async def get_city_housing_data(city_name: str) -> dict:
    """
    Returns normalized housing and cost of living data for any city worldwide.

    Data routing:
      - Austin TX areas: caller should use real_estate.py instead (ACTRIS data)
      - All other cities: fetches live data from Teleport API
      - Fallback: returns HARDCODED_FALLBACK if API is unreachable

    Args:
        city_name: City name in any format (e.g. "Seattle", "san francisco", "Tokyo")

    Returns:
        Dict with unified schema compatible with Austin ACTRIS data structure:
          city, data_source, data_as_of, ListPrice, median_price,
          MedianRentMonthly, AffordabilityScore, housing_score, col_score,
          quality_of_life_score, teleport_scores, summary, fallback_used
    """
    if _is_austin_area(city_name):
        return {
            "city": city_name,
            "note": (
                "Austin TX area detected. Use the real_estate tool for "
                "ACTRIS/MLS data on this location."
            ),
            "redirect": "real_estate",
        }

    slug = await search_city_slug(city_name)

    if slug is None:
        # Best effort: try simple slug from city name
        slug = city_name.lower().strip().replace(" ", "-")

    # Try live Teleport API first
    try:
        result = await _fetch_from_teleport(city_name, slug)
        if result:
            return result
    except Exception:
        pass

    # Fall back to hardcoded data
    return _get_fallback(city_name, slug)


async def _fetch_from_teleport(city_name: str, slug: str) -> Optional[dict]:
    """Calls Teleport /scores/ and /details/ for a given slug."""
    async with httpx.AsyncClient(timeout=_REQUEST_TIMEOUT) as client:
        scores_resp, details_resp = await asyncio.gather(
            client.get(f"{_TELEPORT_BASE}/urban_areas/slug:{slug}/scores/"),
            client.get(f"{_TELEPORT_BASE}/urban_areas/slug:{slug}/details/"),
            return_exceptions=True,
        )

    # Parse scores
    teleport_scores: dict[str, float] = {}
    overall_score: float = 0.0
    housing_score: float = 0.0
    col_score: float = 0.0
    city_display = city_name

    if not isinstance(scores_resp, Exception) and scores_resp.status_code == 200:
        scores_data = scores_resp.json()
        city_display = scores_data.get("ua_name", city_name)
        overall_score = round(scores_data.get("teleport_city_score", 0.0) / 10, 2)
        for cat in scores_data.get("categories", []):
            name = cat.get("name", "").lower().replace(" ", "-")
            score = round(cat.get("score_out_of_10", 0.0), 2)
            teleport_scores[name] = score
            if name == "housing":
                housing_score = score
            elif name == "cost-of-living":
                col_score = score
    else:
        return None  # Slug not found — trigger fallback

    # Parse details for housing cost figures
    median_rent: Optional[int] = None
    list_price: Optional[int] = None

    if not isinstance(details_resp, Exception) and details_resp.status_code == 200:
        details_data = details_resp.json()
        for category in details_data.get("categories", []):
            for data_item in category.get("data", []):
                label = data_item.get("label", "").lower()
                value = data_item.get("currency_dollar_value") or data_item.get("float_value")
                if value is None:
                    continue
                if "median rent" in label or "rent per month" in label:
                    median_rent = int(value)
                elif "median home price" in label or "home price" in label or "house price" in label:
                    list_price = int(value)

    # Derive affordability score (0-10, higher = more affordable)
    # Teleport housing score: high score = good housing = more affordable
    # We map directly; if no housing score default to 5.0
    affordability = round(housing_score if housing_score > 0 else 5.0, 1)

    # Derive col_index approximation (100 = US average)
    # Teleport COL score is 0–10; 10 = cheap, 0 = expensive
    # We invert: col_index ≈ (10 - col_score) * 18 + 20  → rough range 20–200
    col_index = round((10.0 - col_score) * 18.0 + 20.0, 1) if col_score > 0 else 100.0

    # Default rent if not found in details
    if median_rent is None:
        median_rent = _estimate_rent_from_score(col_score)

    # Default list price if not found
    if list_price is None:
        list_price = _estimate_price_from_score(housing_score)

    summary_parts = [f"{city_display} — Teleport city score: {overall_score * 10:.1f}/10."]
    if housing_score:
        summary_parts.append(f"Housing score: {housing_score:.1f}/10.")
    if col_score:
        summary_parts.append(f"Cost of living score: {col_score:.1f}/10.")
    if median_rent:
        summary_parts.append(f"Estimated median rent: ~${median_rent:,}/mo.")

    return {
        "city": city_display,
        "data_source": "Teleport API — live data",
        "data_as_of": "current",
        "ListPrice": list_price,
        "median_price": list_price,
        "MedianRentMonthly": median_rent,
        "AffordabilityScore": affordability,
        "housing_score": housing_score,
        "col_score": col_score,
        "col_index": col_index,
        "quality_of_life_score": overall_score,
        "teleport_scores": teleport_scores,
        "summary": " ".join(summary_parts),
        "fallback_used": False,
        "slug": slug,
    }


def _get_fallback(city_name: str, slug: str) -> dict:
    """Returns hardcoded fallback data, matching slug or closest city name."""
    lower = city_name.lower().strip()

    # Direct slug match
    if slug in HARDCODED_FALLBACK:
        data = dict(HARDCODED_FALLBACK[slug])
        data["fallback_used"] = True
        data["slug"] = slug
        return data

    # Partial name match through fallback values
    for fb_slug, fb_data in HARDCODED_FALLBACK.items():
        if lower in fb_data["city"].lower() or fb_slug.replace("-", " ") in lower:
            data = dict(fb_data)
            data["fallback_used"] = True
            data["slug"] = fb_slug
            return data

    # Generic fallback for unknown city
    return {
        "city": city_name,
        "data_source": "Fallback data (city not in Teleport database)",
        "data_as_of": "estimate",
        "ListPrice": 500_000,
        "median_price": 500_000,
        "MedianRentMonthly": 2000,
        "AffordabilityScore": 5.0,
        "col_score": 5.0,
        "col_index": 100.0,
        "quality_of_life_score": 5.0,
        "teleport_scores": {},
        "summary": f"No Teleport data found for '{city_name}'. Using generic estimates.",
        "fallback_used": True,
        "slug": slug,
    }


def _estimate_rent_from_score(col_score: float) -> int:
    """Estimates median rent from Teleport COL score (10=cheapest, 0=most expensive)."""
    # Linear interpolation: score 10 → $800/mo, score 0 → $4000/mo
    return int(4000 - (col_score / 10.0) * 3200)


def _estimate_price_from_score(housing_score: float) -> int:
    """Estimates home price from Teleport housing score (10=good/cheap, 0=bad/expensive)."""
    # Linear: score 10 → $300k, score 0 → $1.5M
    return int(1_500_000 - (housing_score / 10.0) * 1_200_000)
