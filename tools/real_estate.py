"""
Real Estate Tool — AgentForge integration
==========================================
Feature flag: set ENABLE_REAL_ESTATE=true in .env to activate.
When the flag is absent or false, all functions return a disabled stub
and the graph never routes queries here.

Three capabilities:
  1. search_listings(query)                 — find homes by city/zip/neighborhood
  2. get_neighborhood_snapshot(location)    — market stats for an area
  3. get_listing_details(listing_id)        — full detail for one listing

Provider strategy:
  - MockProvider (default, always safe): realistic sample data for 10 US cities.
    Works offline, zero latency, no API key required.
  - Real provider (future drop-in): swap _PROVIDER to "attom" or "rapidapi" and
    set REAL_ESTATE_API_KEY. The normalize schema is identical.

Data schema (NormalizedListing):
  id, address, city, state, zip, price, bedrooms, bathrooms, sqft,
  price_per_sqft, days_on_market, listing_type, status, year_built,
  hoa_monthly, estimated_monthly_rent, cap_rate_estimate, description

Data schema (NeighborhoodSnapshot):
  city, state, median_price, price_per_sqft, median_dom,
  price_change_yoy_pct, inventory_level, walk_score, listings_count,
  rent_to_price_ratio, market_summary
"""

import os
import time
from datetime import datetime

# ---------------------------------------------------------------------------
# Feature flag
# ---------------------------------------------------------------------------

def is_real_estate_enabled() -> bool:
    """Returns True only when ENABLE_REAL_ESTATE=true in environment."""
    return os.getenv("ENABLE_REAL_ESTATE", "false").strip().lower() == "true"


_FEATURE_DISABLED_RESPONSE = {
    "tool_name": "real_estate",
    "success": False,
    "tool_result_id": "real_estate_disabled",
    "error": "FEATURE_DISABLED",
    "message": (
        "The Real Estate feature is not currently enabled. "
        "Set ENABLE_REAL_ESTATE=true in your environment to activate it."
    ),
}


# ---------------------------------------------------------------------------
# In-memory TTL cache  (5-minute TTL, safe for a single-process server)
# ---------------------------------------------------------------------------

_cache: dict[str, dict] = {}
_CACHE_TTL_SECONDS = 300


def _cache_get(key: str) -> dict | None:
    entry = _cache.get(key)
    if entry and (time.time() - entry["ts"]) < _CACHE_TTL_SECONDS:
        return entry["data"]
    return None


def _cache_set(key: str, data: dict) -> None:
    _cache[key] = {"ts": time.time(), "data": data}


def cache_clear() -> None:
    """Clears the entire in-memory cache. Used in tests."""
    _cache.clear()


# ---------------------------------------------------------------------------
# Mock data  — realistic 2024 US market data for 10 metros
# ---------------------------------------------------------------------------

_MOCK_SNAPSHOTS: dict[str, dict] = {
    "austin": {
        "city": "Austin", "state": "TX",
        "median_price": 485_000, "price_per_sqft": 285,
        "median_dom": 24, "price_change_yoy_pct": -3.2,
        "inventory_level": "low", "walk_score": 48,
        "listings_count": 1_847, "rent_to_price_ratio": 0.48,
        "market_summary": (
            "Austin remains a seller's market with limited inventory. "
            "Prices have cooled slightly YoY (-3.2%) after the pandemic spike, "
            "creating buying opportunities for long-term investors. "
            "Tech sector concentration adds income stability to the renter pool."
        ),
    },
    "san francisco": {
        "city": "San Francisco", "state": "CA",
        "median_price": 1_250_000, "price_per_sqft": 980,
        "median_dom": 18, "price_change_yoy_pct": -5.8,
        "inventory_level": "very low", "walk_score": 88,
        "listings_count": 612, "rent_to_price_ratio": 0.33,
        "market_summary": (
            "San Francisco has seen significant price correction (-5.8% YoY) "
            "driven by remote-work migration. Very low inventory keeps prices "
            "elevated despite demand softening. High rental demand from remaining "
            "tech workforce supports rental yields."
        ),
    },
    "new york": {
        "city": "New York", "state": "NY",
        "median_price": 750_000, "price_per_sqft": 820,
        "median_dom": 31, "price_change_yoy_pct": 1.4,
        "inventory_level": "moderate", "walk_score": 95,
        "listings_count": 4_200, "rent_to_price_ratio": 0.52,
        "market_summary": (
            "NYC market shows resilience with modest 1.4% YoY appreciation. "
            "Moderate inventory gives buyers more negotiating power than 2021–2022. "
            "Strong rental demand across all boroughs supports investor ROI. "
            "High walkability (95) is a key demand driver."
        ),
    },
    "denver": {
        "city": "Denver", "state": "CO",
        "median_price": 520_000, "price_per_sqft": 310,
        "median_dom": 19, "price_change_yoy_pct": -1.7,
        "inventory_level": "low", "walk_score": 60,
        "listings_count": 2_100, "rent_to_price_ratio": 0.46,
        "market_summary": (
            "Denver market stabilizing after rapid appreciation. "
            "Slight YoY decline (-1.7%) brings affordability back into range. "
            "Strong job market in tech and healthcare supports buyer demand. "
            "Low inventory keeps days-on-market competitive at 19 days."
        ),
    },
    "seattle": {
        "city": "Seattle", "state": "WA",
        "median_price": 780_000, "price_per_sqft": 490,
        "median_dom": 14, "price_change_yoy_pct": 2.1,
        "inventory_level": "very low", "walk_score": 73,
        "listings_count": 890, "rent_to_price_ratio": 0.38,
        "market_summary": (
            "Seattle is one of the tightest markets nationally, averaging just "
            "14 days on market. Amazon and Microsoft campuses sustain strong "
            "demand. Prices ticked up 2.1% YoY. Very low inventory means "
            "buyers face competition and often waive contingencies."
        ),
    },
    "miami": {
        "city": "Miami", "state": "FL",
        "median_price": 620_000, "price_per_sqft": 425,
        "median_dom": 38, "price_change_yoy_pct": 4.3,
        "inventory_level": "moderate", "walk_score": 62,
        "listings_count": 3_540, "rent_to_price_ratio": 0.55,
        "market_summary": (
            "Miami continues to attract domestic migration from high-tax states, "
            "pushing prices up 4.3% YoY — one of the strongest gains in the US. "
            "Rising insurance costs are a headwind for buyers. "
            "Strong Airbnb and short-term rental demand boosts investor returns."
        ),
    },
    "chicago": {
        "city": "Chicago", "state": "IL",
        "median_price": 310_000, "price_per_sqft": 195,
        "median_dom": 28, "price_change_yoy_pct": 0.8,
        "inventory_level": "moderate", "walk_score": 78,
        "listings_count": 5_100, "rent_to_price_ratio": 0.68,
        "market_summary": (
            "Chicago offers strong cash-flow potential with the highest "
            "rent-to-price ratio (0.68%) of major metros. Stable pricing "
            "with modest 0.8% YoY appreciation. Property taxes are a key "
            "consideration for investors — factor 2–3% of home value annually."
        ),
    },
    "phoenix": {
        "city": "Phoenix", "state": "AZ",
        "median_price": 415_000, "price_per_sqft": 240,
        "median_dom": 32, "price_change_yoy_pct": -2.1,
        "inventory_level": "high", "walk_score": 41,
        "listings_count": 6_200, "rent_to_price_ratio": 0.50,
        "market_summary": (
            "Phoenix is a buyer's market with the highest inventory of major metros. "
            "Prices down 2.1% YoY after the post-pandemic boom. "
            "Longer days on market (32) gives buyers negotiating leverage. "
            "Strong population growth from CA migration supports long-term demand."
        ),
    },
    "nashville": {
        "city": "Nashville", "state": "TN",
        "median_price": 450_000, "price_per_sqft": 265,
        "median_dom": 21, "price_change_yoy_pct": 1.2,
        "inventory_level": "low", "walk_score": 32,
        "listings_count": 1_650, "rent_to_price_ratio": 0.49,
        "market_summary": (
            "Nashville is a fast-growing Sun Belt market with strong employment "
            "from healthcare, tech, and entertainment sectors. Low inventory and "
            "short DOM (21 days) reflect healthy demand. "
            "No state income tax makes it attractive for relocators."
        ),
    },
    "dallas": {
        "city": "Dallas", "state": "TX",
        "median_price": 395_000, "price_per_sqft": 215,
        "median_dom": 27, "price_change_yoy_pct": -0.5,
        "inventory_level": "moderate", "walk_score": 37,
        "listings_count": 4_800, "rent_to_price_ratio": 0.53,
        "market_summary": (
            "Dallas-Fort Worth offers solid value with near-flat YoY pricing. "
            "Large inventory gives buyers choices without the frenzy of 2021–2022. "
            "Corporate relocations (Goldman Sachs, Oracle, HP) provide long-term "
            "demand foundation. No state income tax is a major draw."
        ),
    },
}

_MOCK_LISTINGS: dict[str, list[dict]] = {
    "austin": [
        {
            "id": "atx-001", "address": "2847 Barton Hills Dr", "city": "Austin", "state": "TX", "zip": "78704",
            "price": 525_000, "bedrooms": 3, "bathrooms": 2.0, "sqft": 1_850, "price_per_sqft": 284,
            "days_on_market": 12, "listing_type": "Single Family", "status": "Active", "year_built": 2018,
            "hoa_monthly": None, "estimated_monthly_rent": 2_800, "cap_rate_estimate": 4.8,
            "description": "Modern craftsman in sought-after 78704. Open floor plan, chef's kitchen, private backyard.",
        },
        {
            "id": "atx-002", "address": "5120 Mueller Blvd #403", "city": "Austin", "state": "TX", "zip": "78723",
            "price": 389_000, "bedrooms": 2, "bathrooms": 2.0, "sqft": 1_100, "price_per_sqft": 354,
            "days_on_market": 34, "listing_type": "Condo", "status": "Active", "year_built": 2021,
            "hoa_monthly": 285, "estimated_monthly_rent": 2_200, "cap_rate_estimate": 4.2,
            "description": "Luxury condo in Mueller district. Rooftop deck, concierge, walkable to restaurants.",
        },
        {
            "id": "atx-003", "address": "3901 Govalle Ave", "city": "Austin", "state": "TX", "zip": "78702",
            "price": 595_000, "bedrooms": 4, "bathrooms": 3.0, "sqft": 2_200, "price_per_sqft": 270,
            "days_on_market": 7, "listing_type": "Single Family", "status": "Active", "year_built": 2016,
            "hoa_monthly": None, "estimated_monthly_rent": 3_200, "cap_rate_estimate": 5.0,
            "description": "Spacious east Austin home. ADU potential, mature trees, 5 min from downtown.",
        },
        {
            "id": "atx-004", "address": "1204 W 6th St #8", "city": "Austin", "state": "TX", "zip": "78703",
            "price": 699_000, "bedrooms": 3, "bathrooms": 2.5, "sqft": 1_950, "price_per_sqft": 358,
            "days_on_market": 19, "listing_type": "Townhouse", "status": "Active", "year_built": 2020,
            "hoa_monthly": 175, "estimated_monthly_rent": 3_600, "cap_rate_estimate": 4.5,
            "description": "Premium Clarksville townhome. Rooftop terrace with downtown skyline views.",
        },
        {
            "id": "atx-005", "address": "7824 Manchaca Rd", "city": "Austin", "state": "TX", "zip": "78745",
            "price": 349_000, "bedrooms": 3, "bathrooms": 2.0, "sqft": 1_450, "price_per_sqft": 241,
            "days_on_market": 42, "listing_type": "Single Family", "status": "Price Reduced", "year_built": 2003,
            "hoa_monthly": None, "estimated_monthly_rent": 2_100, "cap_rate_estimate": 5.4,
            "description": "Best value in South Austin. Newly renovated kitchen, large yard, no HOA.",
        },
    ],
    "san francisco": [
        {
            "id": "sfo-001", "address": "1847 Castro St", "city": "San Francisco", "state": "CA", "zip": "94114",
            "price": 1_450_000, "bedrooms": 3, "bathrooms": 2.0, "sqft": 1_600, "price_per_sqft": 906,
            "days_on_market": 9, "listing_type": "Single Family", "status": "Active", "year_built": 1924,
            "hoa_monthly": None, "estimated_monthly_rent": 5_200, "cap_rate_estimate": 3.4,
            "description": "Classic Victorian in the Castro. Period details preserved, updated kitchen and baths.",
        },
        {
            "id": "sfo-002", "address": "488 Folsom St #2105", "city": "San Francisco", "state": "CA", "zip": "94105",
            "price": 1_100_000, "bedrooms": 2, "bathrooms": 2.0, "sqft": 1_050, "price_per_sqft": 1_048,
            "days_on_market": 22, "listing_type": "Condo", "status": "Active", "year_built": 2018,
            "hoa_monthly": 890, "estimated_monthly_rent": 4_800, "cap_rate_estimate": 3.2,
            "description": "Luxury high-rise with bay views. Full-service building, concierge, parking included.",
        },
        {
            "id": "sfo-003", "address": "222 Dolores St #7", "city": "San Francisco", "state": "CA", "zip": "94103",
            "price": 875_000, "bedrooms": 1, "bathrooms": 1.0, "sqft": 780, "price_per_sqft": 1_122,
            "days_on_market": 14, "listing_type": "Condo", "status": "Active", "year_built": 2015,
            "hoa_monthly": 620, "estimated_monthly_rent": 3_600, "cap_rate_estimate": 3.0,
            "description": "Designer Mission condo. Chef's kitchen, private patio, storage included.",
        },
    ],
    "new york": [
        {
            "id": "nyc-001", "address": "200 Water St #8B", "city": "New York", "state": "NY", "zip": "10038",
            "price": 895_000, "bedrooms": 2, "bathrooms": 2.0, "sqft": 1_100, "price_per_sqft": 814,
            "days_on_market": 18, "listing_type": "Condo", "status": "Active", "year_built": 2006,
            "hoa_monthly": 1_240, "estimated_monthly_rent": 5_800, "cap_rate_estimate": 4.6,
            "description": "FiDi condo with East River views. Doorman, gym, roof deck. Minutes from Wall St.",
        },
        {
            "id": "nyc-002", "address": "78 N 7th St #4D", "city": "Brooklyn", "state": "NY", "zip": "11249",
            "price": 1_100_000, "bedrooms": 3, "bathrooms": 2.0, "sqft": 1_350, "price_per_sqft": 815,
            "days_on_market": 25, "listing_type": "Condo", "status": "Active", "year_built": 2019,
            "hoa_monthly": 780, "estimated_monthly_rent": 5_500, "cap_rate_estimate": 4.2,
            "description": "Williamsburg luxury condo. Industrial chic design, private outdoor space.",
        },
        {
            "id": "nyc-003", "address": "310 W 55th St #7C", "city": "New York", "state": "NY", "zip": "10019",
            "price": 649_000, "bedrooms": 1, "bathrooms": 1.0, "sqft": 650, "price_per_sqft": 998,
            "days_on_market": 31, "listing_type": "Coop", "status": "Active", "year_built": 1967,
            "hoa_monthly": 1_450, "estimated_monthly_rent": 3_800, "cap_rate_estimate": 3.5,
            "description": "Classic midtown co-op. Full-service white glove building, 4 blocks from Central Park.",
        },
    ],
    "denver": [
        {
            "id": "den-001", "address": "2345 Larimer St #601", "city": "Denver", "state": "CO", "zip": "80205",
            "price": 545_000, "bedrooms": 2, "bathrooms": 2.0, "sqft": 1_400, "price_per_sqft": 389,
            "days_on_market": 11, "listing_type": "Condo", "status": "Active", "year_built": 2017,
            "hoa_monthly": 340, "estimated_monthly_rent": 2_600, "cap_rate_estimate": 4.3,
            "description": "RiNo district condo. Exposed brick, mountain views, walkable to food & art scene.",
        },
        {
            "id": "den-002", "address": "4812 W 32nd Ave", "city": "Denver", "state": "CO", "zip": "80212",
            "price": 698_000, "bedrooms": 4, "bathrooms": 3.0, "sqft": 2_400, "price_per_sqft": 291,
            "days_on_market": 17, "listing_type": "Single Family", "status": "Active", "year_built": 2015,
            "hoa_monthly": None, "estimated_monthly_rent": 3_400, "cap_rate_estimate": 4.8,
            "description": "Highland neighborhood gem. Chef's kitchen, finished basement, large backyard deck.",
        },
    ],
    "seattle": [
        {
            "id": "sea-001", "address": "1417 NW 63rd St", "city": "Seattle", "state": "WA", "zip": "98107",
            "price": 895_000, "bedrooms": 3, "bathrooms": 2.0, "sqft": 1_750, "price_per_sqft": 511,
            "days_on_market": 8, "listing_type": "Single Family", "status": "Active", "year_built": 2014,
            "hoa_monthly": None, "estimated_monthly_rent": 3_800, "cap_rate_estimate": 4.1,
            "description": "Ballard Craftsman with Puget Sound views. Eco-smart systems, attached garage.",
        },
        {
            "id": "sea-002", "address": "220 2nd Ave S #1102", "city": "Seattle", "state": "WA", "zip": "98104",
            "price": 699_000, "bedrooms": 2, "bathrooms": 2.0, "sqft": 1_200, "price_per_sqft": 583,
            "days_on_market": 13, "listing_type": "Condo", "status": "Active", "year_built": 2020,
            "hoa_monthly": 595, "estimated_monthly_rent": 3_200, "cap_rate_estimate": 3.9,
            "description": "Pioneer Square luxury condo. Amazon HQ walking distance, Elliott Bay views.",
        },
    ],
    "miami": [
        {
            "id": "mia-001", "address": "1600 Brickell Ave #3204", "city": "Miami", "state": "FL", "zip": "33129",
            "price": 1_200_000, "bedrooms": 3, "bathrooms": 3.0, "sqft": 2_100, "price_per_sqft": 571,
            "days_on_market": 22, "listing_type": "Condo", "status": "Active", "year_built": 2022,
            "hoa_monthly": 1_850, "estimated_monthly_rent": 7_500, "cap_rate_estimate": 5.2,
            "description": "Brickell ultra-luxury unit. Bayfront views, private balcony, 5-star amenities.",
        },
        {
            "id": "mia-002", "address": "355 NE 1st Ave #712", "city": "Miami", "state": "FL", "zip": "33132",
            "price": 435_000, "bedrooms": 1, "bathrooms": 1.0, "sqft": 780, "price_per_sqft": 558,
            "days_on_market": 40, "listing_type": "Condo", "status": "Active", "year_built": 2014,
            "hoa_monthly": 680, "estimated_monthly_rent": 2_800, "cap_rate_estimate": 4.8,
            "description": "Downtown Miami studio + den. Airbnb-allowed building, strong short-term rental income.",
        },
    ],
    "chicago": [
        {
            "id": "chi-001", "address": "900 N Michigan Ave #2400", "city": "Chicago", "state": "IL", "zip": "60611",
            "price": 625_000, "bedrooms": 2, "bathrooms": 2.0, "sqft": 1_800, "price_per_sqft": 347,
            "days_on_market": 29, "listing_type": "Condo", "status": "Active", "year_built": 1991,
            "hoa_monthly": 980, "estimated_monthly_rent": 4_200, "cap_rate_estimate": 5.8,
            "description": "Magnificent Mile full-floor unit. Lake Michigan views, white glove service.",
        },
        {
            "id": "chi-002", "address": "2140 N Damen Ave", "city": "Chicago", "state": "IL", "zip": "60647",
            "price": 485_000, "bedrooms": 3, "bathrooms": 2.5, "sqft": 2_100, "price_per_sqft": 231,
            "days_on_market": 20, "listing_type": "Single Family", "status": "Active", "year_built": 2008,
            "hoa_monthly": None, "estimated_monthly_rent": 3_200, "cap_rate_estimate": 6.2,
            "description": "Bucktown greystone townhome. Finished basement, private garage, top-rated schools.",
        },
    ],
    "phoenix": [
        {
            "id": "phx-001", "address": "4820 E Camelback Rd", "city": "Phoenix", "state": "AZ", "zip": "85018",
            "price": 625_000, "bedrooms": 4, "bathrooms": 3.0, "sqft": 2_800, "price_per_sqft": 223,
            "days_on_market": 38, "listing_type": "Single Family", "status": "Price Reduced", "year_built": 2005,
            "hoa_monthly": 95, "estimated_monthly_rent": 3_200, "cap_rate_estimate": 4.9,
            "description": "Arcadia location with Camelback Mountain views. Pool, 3-car garage, gourmet kitchen.",
        },
    ],
    "nashville": [
        {
            "id": "nas-001", "address": "600 12th Ave S #405", "city": "Nashville", "state": "TN", "zip": "37203",
            "price": 489_000, "bedrooms": 2, "bathrooms": 2.0, "sqft": 1_350, "price_per_sqft": 362,
            "days_on_market": 15, "listing_type": "Condo", "status": "Active", "year_built": 2020,
            "hoa_monthly": 320, "estimated_monthly_rent": 2_800, "cap_rate_estimate": 5.1,
            "description": "The Gulch walkable condo. No-state-income-tax advantage, steps to Broadway.",
        },
    ],
    "dallas": [
        {
            "id": "dfw-001", "address": "3421 McKinney Ave #207", "city": "Dallas", "state": "TX", "zip": "75204",
            "price": 389_000, "bedrooms": 2, "bathrooms": 2.0, "sqft": 1_200, "price_per_sqft": 324,
            "days_on_market": 21, "listing_type": "Condo", "status": "Active", "year_built": 2019,
            "hoa_monthly": 290, "estimated_monthly_rent": 2_400, "cap_rate_estimate": 5.4,
            "description": "Uptown Dallas condo. Pet-friendly, resort-style amenities, walkable to dining.",
        },
    ],
}


def _normalize_city(location: str) -> str:
    """Maps query string to a canonical city key in mock data."""
    loc = location.lower().strip()
    mapping = {
        "atx": "austin", "austin tx": "austin", "austin, tx": "austin",
        "sf": "san francisco", "sfo": "san francisco", "san francisco ca": "san francisco",
        "nyc": "new york", "new york city": "new york", "manhattan": "new york", "brooklyn": "new york",
        "denver co": "denver", "denver, co": "denver",
        "seattle wa": "seattle", "seattle, wa": "seattle",
        "miami fl": "miami", "miami, fl": "miami",
        "chicago il": "chicago", "chicago, il": "chicago",
        "phoenix az": "phoenix", "phoenix, az": "phoenix",
        "nashville tn": "nashville", "nashville, tn": "nashville",
        "dallas tx": "dallas", "dallas, tx": "dallas", "dfw": "dallas",
    }
    if loc in mapping:
        return mapping[loc]
    for city_key in _MOCK_SNAPSHOTS:
        if city_key in loc:
            return city_key
    return ""


# ---------------------------------------------------------------------------
# Public tool functions  — all follow the standard tool result schema
# ---------------------------------------------------------------------------

async def get_neighborhood_snapshot(location: str) -> dict:
    """
    Returns market-level stats for a city or neighborhood.
    Covers: median price, DOM, YoY change, inventory level, walk score,
    rent-to-price ratio, market summary.
    """
    if not is_real_estate_enabled():
        return _FEATURE_DISABLED_RESPONSE

    location = location.strip()
    tool_result_id = f"re_snapshot_{location.lower().replace(' ', '_')}_{int(datetime.utcnow().timestamp())}"

    cache_key = f"snapshot:{location.lower()}"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    city_key = _normalize_city(location)
    snap = _MOCK_SNAPSHOTS.get(city_key)

    if not snap:
        result = {
            "tool_name": "real_estate",
            "success": False,
            "tool_result_id": tool_result_id,
            "error": "LOCATION_NOT_FOUND",
            "message": (
                f"No data found for '{location}'. "
                f"Supported cities: {', '.join(c.title() for c in _MOCK_SNAPSHOTS)}."
            ),
        }
        return result

    monthly_rent_estimate = round(snap["median_price"] * snap["rent_to_price_ratio"] / 100, 0)
    gross_yield = round(snap["rent_to_price_ratio"] * 12 / 100 * 100, 2)

    result = {
        "tool_name": "real_estate",
        "success": True,
        "tool_result_id": tool_result_id,
        "timestamp": datetime.utcnow().isoformat(),
        "result": {
            "location": f"{snap['city']}, {snap['state']}",
            "median_price": snap["median_price"],
            "price_per_sqft": snap["price_per_sqft"],
            "median_days_on_market": snap["median_dom"],
            "price_change_yoy_pct": snap["price_change_yoy_pct"],
            "inventory_level": snap["inventory_level"],
            "walk_score": snap["walk_score"],
            "active_listings_count": snap["listings_count"],
            "estimated_median_monthly_rent": monthly_rent_estimate,
            "gross_rental_yield_pct": gross_yield,
            "market_summary": snap["market_summary"],
            "data_source": "MockProvider v1 — realistic 2024 US market estimates",
        },
    }
    _cache_set(cache_key, result)
    return result


async def search_listings(query: str, max_results: int = 5) -> dict:
    """
    Searches for listings matching a location query.
    Returns up to max_results normalized listings with key metrics.
    """
    if not is_real_estate_enabled():
        return _FEATURE_DISABLED_RESPONSE

    query = query.strip()
    tool_result_id = f"re_search_{query.lower().replace(' ', '_')}_{int(datetime.utcnow().timestamp())}"

    cache_key = f"search:{query.lower()}:{max_results}"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    city_key = _normalize_city(query)
    listings = _MOCK_LISTINGS.get(city_key, [])

    if not listings:
        all_cities = list(_MOCK_LISTINGS.keys())
        result = {
            "tool_name": "real_estate",
            "success": False,
            "tool_result_id": tool_result_id,
            "error": "NO_LISTINGS_FOUND",
            "message": (
                f"No listings found for '{query}'. "
                f"Try one of: {', '.join(c.title() for c in all_cities)}."
            ),
        }
        return result

    capped = listings[:max_results]
    result = {
        "tool_name": "real_estate",
        "success": True,
        "tool_result_id": tool_result_id,
        "timestamp": datetime.utcnow().isoformat(),
        "result": {
            "query": query,
            "total_returned": len(capped),
            "listings": capped,
            "data_source": "MockProvider v1 — realistic 2024 US market estimates",
        },
    }
    _cache_set(cache_key, result)
    return result


async def get_listing_details(listing_id: str) -> dict:
    """
    Returns full detail for a single listing by its ID (e.g. 'atx-001').
    """
    if not is_real_estate_enabled():
        return _FEATURE_DISABLED_RESPONSE

    listing_id = listing_id.strip().lower()
    tool_result_id = f"re_detail_{listing_id}_{int(datetime.utcnow().timestamp())}"

    cache_key = f"detail:{listing_id}"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    for city_listings in _MOCK_LISTINGS.values():
        for listing in city_listings:
            if listing["id"].lower() == listing_id:
                # Enrich with affordability metrics
                enriched = dict(listing)
                monthly_payment_est = round(listing["price"] * 0.8 * 0.00532, 0)  # ~6.5% 30yr, 20% down
                annual_rent = listing["estimated_monthly_rent"] * 12
                enriched["estimated_monthly_mortgage"] = monthly_payment_est
                enriched["annual_gross_rental_income"] = annual_rent
                enriched["gross_cap_rate_pct"] = listing["cap_rate_estimate"]

                result = {
                    "tool_name": "real_estate",
                    "success": True,
                    "tool_result_id": tool_result_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "result": enriched,
                }
                _cache_set(cache_key, result)
                return result

    result = {
        "tool_name": "real_estate",
        "success": False,
        "tool_result_id": tool_result_id,
        "error": "LISTING_NOT_FOUND",
        "message": (
            f"Listing '{listing_id}' not found. "
            "Use search_listings first to get valid listing IDs."
        ),
    }
    return result


async def compare_neighborhoods(location_a: str, location_b: str) -> dict:
    """
    Compares two cities/neighborhoods side by side on key investment metrics.
    Returns a structured comparison useful for commute/affordability tradeoffs.
    """
    if not is_real_estate_enabled():
        return _FEATURE_DISABLED_RESPONSE

    tool_result_id = f"re_compare_{int(datetime.utcnow().timestamp())}"

    snap_a = await get_neighborhood_snapshot(location_a)
    snap_b = await get_neighborhood_snapshot(location_b)

    failed = []
    if not snap_a.get("success"):
        failed.append(location_a)
    if not snap_b.get("success"):
        failed.append(location_b)

    if failed:
        return {
            "tool_name": "real_estate",
            "success": False,
            "tool_result_id": tool_result_id,
            "error": "LOCATION_NOT_FOUND",
            "message": f"Could not find data for: {', '.join(failed)}.",
        }

    a = snap_a["result"]
    b = snap_b["result"]

    def _winner(val_a, val_b, lower_is_better: bool = False):
        if lower_is_better:
            return a["location"] if val_a < val_b else b["location"]
        return a["location"] if val_a > val_b else b["location"]

    comparison = {
        "location_a": a["location"],
        "location_b": b["location"],
        "metrics": {
            "median_price": {"a": a["median_price"], "b": b["median_price"],
                             "more_affordable": _winner(a["median_price"], b["median_price"], lower_is_better=True)},
            "price_per_sqft": {"a": a["price_per_sqft"], "b": b["price_per_sqft"],
                               "more_affordable": _winner(a["price_per_sqft"], b["price_per_sqft"], lower_is_better=True)},
            "gross_rental_yield_pct": {"a": a["gross_rental_yield_pct"], "b": b["gross_rental_yield_pct"],
                                       "higher_yield": _winner(a["gross_rental_yield_pct"], b["gross_rental_yield_pct"])},
            "days_on_market": {"a": a["median_days_on_market"], "b": b["median_days_on_market"],
                               "less_competitive": _winner(a["median_days_on_market"], b["median_days_on_market"])},
            "walk_score": {"a": a["walk_score"], "b": b["walk_score"],
                           "more_walkable": _winner(a["walk_score"], b["walk_score"])},
            "yoy_price_change_pct": {"a": a["price_change_yoy_pct"], "b": b["price_change_yoy_pct"]},
            "inventory": {"a": a["inventory_level"], "b": b["inventory_level"]},
        },
        "summaries": {
            a["location"]: a["market_summary"],
            b["location"]: b["market_summary"],
        },
        "data_source": "MockProvider v1 — realistic 2024 US market estimates",
    }

    result = {
        "tool_name": "real_estate",
        "success": True,
        "tool_result_id": tool_result_id,
        "timestamp": datetime.utcnow().isoformat(),
        "result": comparison,
    }
    return result
