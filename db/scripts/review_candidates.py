"""Re-review rejected candidates and approve valid cross-platform matches."""
from __future__ import annotations

import asyncio
import calendar
import json
import re
import unicodedata
from pathlib import Path

import httpx
from dotenv import load_dotenv

from auth import require_env

_CANDIDATES_PATH = Path("db/data/candidates.json")
_MATCHES_PATH = Path("db/data/matches.json")
_REJECTED_PATH = Path("db/data/rejected_matches.json")

# ---- False positive series ----

FALSE_POSITIVE_SERIES = {
    "KXMLBEXTRAS": "Kalshi is extra innings; Poly is F5 winner — different event",
    "KXATPSETWINNER": "Kalshi is set 1 winner; Poly is game spread -1.5 — different bet type",
    "KXWTASETWINNER": "Kalshi is set 1 winner; Poly is game spread -1.5 — different bet type",
    "KXUFCVICROUND": "Kalshi is round of victory; Poly is method of victory (KO/TKO/DQ) — different bet type",
    "KXWNBASPREAD": "Spread lines don't match between platforms",
    "KXWCADVANCE": "Kalshi is match winner; Poly is spread -2.5 — different bet type",
    "KXWCDELAY": "Kalshi is weather delay; Poly is spread — different event",
    "KXDESANTISRUN": "Kalshi is DeSantis-specific; Poly markets are for other candidates — no matching outcome",
    "KXTRUMPPARDON": "Kalshi is pardons; Poly is admin departures — different event",
    "KXESVI": "Kalshi is Elder Scrolls VI; Poly is GTA VI — different game",
    "KXCODINGMODEL": "Kalshi is best coding model; Poly is overall #1 AI model — different question",
}

FALSE_POSITIVE_SLUGS = {
    "KXNBASUMMERGAME": "NBA Summer League Chicago matched to MLB Athletics vs White Sox — different sport/event",
    "KXITFMATCH": "ITF tennis matched to UFC fight — different sport",
    "KXGHANAPRES": "Ghana presidential matched to UK Clacton by-election — different country",
    "KXPHILIPPINESSENATE": "Philippine Senate matched to Maine Senate — different country",
    "KXPRESPERSON": "2028 presidential matched to Senate midterm — different election",
    "KXRENOMAYOR": "Reno mayoral matched to LA mayoral — different city",
    "KXSENATEWYD": "Wyoming Dem Senate matched to Maine Dem Senate — different state",
    "KXALASKAHOUSE": "Alaska House specific matched to US House Midterm general — different scope",
    "SENATEAK": "Kalshi is 2028 Alaska Senate; Poly is 2026 — different election year",
}

WEATHER_FALSE_POSITIVE_SERIES = {"KXHIGHPHIL", "KXHIGHTSFO", "KXTEMPLAXH"}

SPORT_MONEYLINE_SERIES = {
    "KXATPMATCH", "KXATPCHALLENGERMATCH", "KXWTAMATCH",
    "KXCS2GAME", "KXVALORANTGAME", "KXLOLGAME",
    "KXNPBGAME", "KXT20MATCH",
}

F5_SERIES = {"KXMLBF5"}

DATE_BUCKETED_SERIES = {
    "KXIMPEACH", "KXKASHOUT", "KXHEGSETHOUT", "KXSAVEACT",
    "KXBTCMAX150", "KXIPOANTHROPIC", "KXIPOOPENAI",
}

MULTI_OUTCOME_SERIES = {
    "KXBTCMAXY", "KXTIME", "KXTOPARTIST", "KXIPO",
    "KXBIGBROTHERELIMINATION", "KXLIUSAWINNERS", "KXATP1RANK",
}

POLITICAL_SERIES = {
    "GOVPARTYOH", "GOVPARTYKS", "GOVPARTYIA", "GOVPARTYGA",
    "GOVPARTYWI", "KXGOVCA", "GOVPARTYNV", "GOVPARTYAZ",
    "GOVPARTYMI", "GOVPARTYSD", "GOVPARTYOK", "GOVPARTYFL",
    "SENATENH", "SENATENC", "SENATETX", "SENATEOHS",
    "SENATENE", "SENATEIA", "SENATEGA", "SENATEMN", "SENATEMI",
    "SENATEAK",
    "KXBRPRES", "KXFRENCHPRES", "KXISRAELPM",
}


# ---- Helpers ----

async def fetch_poly_market_detail(client: httpx.AsyncClient, slug: str) -> dict | None:
    base = "https://gateway.polymarket.us"
    try:
        resp = await client.get(f"{base}/v1/market/slug/{slug}", timeout=10.0)
        if resp.status_code != 200:
            return None
        return resp.json().get("market", {})
    except Exception:
        return None


def get_poly_yes_team(market_detail: dict) -> str | None:
    for side in market_detail.get("marketSides", []):
        if side.get("long"):
            team = side.get("team", {})
            return team.get("abbreviation", "").upper() if team else None
    return None


def extract_team_abbr_from_ticker(ticker: str) -> str:
    return ticker.rsplit("-", 1)[-1].upper()


def extract_team_from_question(question: str) -> str | None:
    """Extract the YES team from a Poly F5 question like 'Will the San Francisco Giants win the first 5 innings...'"""
    m = re.match(r"Will the (.+?) (?:win|cover|beat)", question, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    return None


# MLB team name → common abbreviations
_MLB_TEAM_ABBRS = {
    "arizona diamondbacks": "ARI", "atlanta braves": "ATL",
    "baltimore orioles": "BAL", "boston red sox": "BOS",
    "chicago cubs": "CHC", "chicago white sox": "CWS",
    "cincinnati reds": "CIN", "cleveland guardians": "CLE",
    "colorado rockies": "COL", "detroit tigers": "DET",
    "houston astros": "HOU", "kansas city royals": "KC",
    "los angeles angels": "LAA", "los angeles dodgers": "LAD",
    "miami marlins": "MIA", "milwaukee brewers": "MIL",
    "minnesota twins": "MIN", "new york mets": "NYM",
    "new york yankees": "NYY", "oakland athletics": "OAK",
    "philadelphia phillies": "PHI", "pittsburgh pirates": "PIT",
    "san diego padres": "SD", "san francisco giants": "SF",
    "seattle mariners": "SEA", "st. louis cardinals": "STL",
    "st louis cardinals": "STL", "tampa bay rays": "TB",
    "texas rangers": "TEX", "toronto blue jays": "TOR",
    "washington nationals": "WSH", "athletics": "OAK",
}


def team_name_to_abbr(name: str) -> str | None:
    low = name.lower().strip()
    if low in _MLB_TEAM_ABBRS:
        return _MLB_TEAM_ABBRS[low]
    for full_name, abbr in _MLB_TEAM_ABBRS.items():
        if low in full_name or full_name.endswith(low):
            return abbr
    return None


def extract_name_from_slug(slug: str) -> str | None:
    """Extract the encoded name suffix from a Poly slug.
    e.g., 'tpoyc-2026-badbun' → 'badbun', 'ipcc-2026ipos-deel' → 'deel'
    """
    parts = slug.rsplit("-", 1)
    if len(parts) == 2:
        return parts[1].lower()
    return None


def _strip_accents(s: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", s)
        if unicodedata.category(c) != "Mn"
    )


def slug_name_matches_kalshi_title(slug_name: str, kalshi_title: str) -> bool:
    """Check if a slug-encoded name matches a Kalshi sub-market title."""
    k_lower = _strip_accents(kalshi_title.lower().strip())
    slug_name = _strip_accents(slug_name)
    k_parts = k_lower.split()

    if len(slug_name) <= 3:
        return k_lower.startswith(slug_name)

    if len(k_parts) >= 2:
        first = k_parts[0][:3]
        last = k_parts[-1][:3]
        if slug_name == first + last:
            return True
        second = k_parts[1][:3]
        if slug_name == first + second:
            return True

    if k_lower.replace(" ", "").startswith(slug_name):
        return True
    if slug_name in k_lower.replace(" ", ""):
        return True
    if slug_name == k_lower:
        return True

    # Bitcoin price matching: slug "200k" ↔ title "Above $199,999.99"
    price_match = re.match(r"^(\d+)k$", slug_name)
    if price_match:
        target = int(price_match.group(1)) * 1000 - 0.01
        price_in_title = re.search(r"\$([\d,]+\.?\d*)", kalshi_title)
        if price_in_title:
            k_price = float(price_in_title.group(1).replace(",", ""))
            if abs(k_price - target) < 1:
                return True

    return False


def match_party_from_slug(slug: str) -> str | None:
    """Extract party from political slug suffix like '-rep' or '-dem'."""
    if slug.endswith("-rep"):
        return "republican"
    if slug.endswith("-dem"):
        return "democratic"
    if slug.endswith("-ind"):
        return "independent"
    return None


def find_kalshi_party_ticker(kalshi_markets: list[dict], party: str) -> tuple[str, str] | None:
    """Find the Kalshi ticker for a given party."""
    for km in kalshi_markets:
        title = km.get("title", "").lower()
        if party in title:
            return km["ticker"], km["title"]
        # Also check ticker suffix
        suffix = km["ticker"].rsplit("-", 1)[-1].upper()
        party_suffixes = {"republican": {"REP", "R", "GOP"}, "democratic": {"DEM", "D"}}
        if suffix in party_suffixes.get(party, set()):
            return km["ticker"], km["title"]
    return None


def is_primary_mismatch(candidate: dict) -> bool:
    slug = candidate["polymarket"]["slug"]
    q = candidate["polymarket"]["question"].lower()
    k_title = candidate["kalshi_event"]["title"].lower()
    if "primary" in q and "primary" not in k_title:
        return True
    if "primary" in k_title and "primary" not in q:
        return True
    if ("nominee" in q or "primary" in slug) and "nominee" not in k_title and "primary" not in k_title:
        return True
    return False


# ---- Processors ----

async def process_sport_moneyline(
    candidate: dict,
    client: httpx.AsyncClient,
) -> tuple[list[dict], list[dict]]:
    matches, rejects = [], []
    slug = candidate["polymarket"]["slug"]
    kalshi_markets = candidate["kalshi_markets"]
    k_title = candidate["kalshi_event"]["title"]
    p_question = candidate["polymarket"]["question"]

    detail = await fetch_poly_market_detail(client, slug)
    if not detail:
        rejects.append({
            "kalshi_event_ticker": candidate["kalshi_event"]["event_ticker"],
            "polymarket_slug": slug,
            "reason": "Could not fetch Poly market detail for direction",
        })
        return matches, rejects

    poly_yes_abbr = get_poly_yes_team(detail)
    if not poly_yes_abbr:
        rejects.append({
            "kalshi_event_ticker": candidate["kalshi_event"]["event_ticker"],
            "polymarket_slug": slug,
            "reason": f"No marketSides with long=true. Q: {p_question}",
        })
        return matches, rejects

    for km in kalshi_markets:
        ticker = km["ticker"]
        k_team = extract_team_abbr_from_ticker(ticker)
        direction = "kalshi_yes_eq_poly_yes" if k_team == poly_yes_abbr else "kalshi_yes_eq_poly_no"
        matches.append({
            "id": f"{slug}-{k_team.lower()}",
            "kalshi_ticker": ticker,
            "polymarket_slug": slug,
            "direction": direction,
            "notes": f"Kalshi YES = {k_team}, Poly YES = {poly_yes_abbr}. K: {k_title}. P: {p_question}",
        })

    return matches, rejects


async def process_mlb_f5(
    candidate: dict,
    client: httpx.AsyncClient,
) -> tuple[list[dict], list[dict]]:
    matches, rejects = [], []
    slug = candidate["polymarket"]["slug"]
    kalshi_markets = candidate["kalshi_markets"]
    p_question = candidate["polymarket"]["question"]
    k_title = candidate["kalshi_event"]["title"]
    event_ticker = candidate["kalshi_event"]["event_ticker"]

    # Try marketSides first
    detail = await fetch_poly_market_detail(client, slug)
    poly_yes_abbr = None
    if detail:
        poly_yes_abbr = get_poly_yes_team(detail)

    # Fallback: extract team from question text
    if not poly_yes_abbr:
        team_name = extract_team_from_question(p_question)
        if team_name:
            poly_yes_abbr = team_name_to_abbr(team_name)
            if poly_yes_abbr:
                print(f"  F5 fallback: '{team_name}' → {poly_yes_abbr}")

    if not poly_yes_abbr:
        rejects.append({
            "kalshi_event_ticker": event_ticker,
            "polymarket_slug": slug,
            "reason": f"Could not determine Poly YES side for F5 — question: {p_question}",
        })
        return matches, rejects

    for km in kalshi_markets:
        ticker = km["ticker"]
        k_team = extract_team_abbr_from_ticker(ticker)
        if k_team == "TIE":
            continue
        direction = "kalshi_yes_eq_poly_yes" if k_team == poly_yes_abbr else "kalshi_yes_eq_poly_no"
        matches.append({
            "id": f"{slug}-f5-{k_team.lower()}",
            "kalshi_ticker": ticker,
            "polymarket_slug": slug,
            "direction": direction,
            "notes": f"MLB F5: Kalshi YES = {k_team} wins F5, Poly YES = {poly_yes_abbr} wins F5. K: {k_title}. P: {p_question}",
        })

    return matches, rejects


def match_date_windows(kalshi_markets: list[dict], poly_slug: str) -> str | None:
    # Extract date from Poly slug
    date_match = re.search(r"(\d{2})-(\d{2})-(\d{4})$", poly_slug)
    if date_match:
        p_month, p_day, p_year = int(date_match.group(1)), int(date_match.group(2)), int(date_match.group(3))
    else:
        date_match = re.search(r"(\d{4})-(\d{2})-(\d{2})$", poly_slug)
        if date_match:
            p_month, p_day, p_year = int(date_match.group(2)), int(date_match.group(3)), int(date_match.group(1))
        else:
            return None

    for km in kalshi_markets:
        title = km.get("title", "").lower()
        ticker = km["ticker"]

        before_match = re.search(r"before\s+(\w+)\s+(\d+)", title)
        if not before_match:
            continue

        month_str = before_match.group(1)
        day_or_year = int(before_match.group(2))

        month_map = {
            "jan": 1, "january": 1, "feb": 2, "february": 2,
            "mar": 3, "march": 3, "apr": 4, "april": 4,
            "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
            "aug": 8, "august": 8, "sep": 9, "september": 9,
            "oct": 10, "october": 10, "nov": 11, "november": 11,
            "dec": 12, "december": 12,
        }
        k_month = month_map.get(month_str.lower())
        if k_month is None:
            continue

        if day_or_year > 31:
            k_day = 1
            k_year = day_or_year
        else:
            k_day = day_or_year
            year_match = re.search(r"(\d{4})", title[before_match.end():])
            k_year = int(year_match.group(1)) if year_match else p_year

        if k_day == 1:
            prev_month = k_month - 1
            prev_year = k_year
            if prev_month == 0:
                prev_month = 12
                prev_year -= 1
            last_day = calendar.monthrange(prev_year, prev_month)[1]
            if p_month == prev_month and p_year == prev_year and abs(last_day - p_day) <= 3:
                return ticker
        else:
            # "Before Jan 4" → aligns with Dec 31 (3 days tolerance)
            if k_month == 1 and k_day <= 5 and p_month == 12 and p_day >= 28 and p_year == k_year - 1:
                return ticker
            if p_month == k_month and abs(p_day - (k_day - 1)) <= 1 and p_year == k_year:
                return ticker

    return None


async def process_date_bucketed(candidate: dict) -> tuple[list[dict], list[dict]]:
    matches, rejects = [], []
    slug = candidate["polymarket"]["slug"]
    kalshi_markets = candidate["kalshi_markets"]
    event_ticker = candidate["kalshi_event"]["event_ticker"]
    k_title = candidate["kalshi_event"]["title"]
    p_question = candidate["polymarket"]["question"]

    matched_ticker = match_date_windows(kalshi_markets, slug)
    if matched_ticker:
        km_title = next((km["title"] for km in kalshi_markets if km["ticker"] == matched_ticker), "")
        matches.append({
            "id": f"{slug}-{event_ticker.lower()}",
            "kalshi_ticker": matched_ticker,
            "polymarket_slug": slug,
            "direction": "kalshi_yes_eq_poly_yes",
            "notes": f"Date-bucketed: Kalshi '{km_title}' ↔ Poly slug date. K: {k_title}. P: {p_question}",
        })
    else:
        rejects.append({
            "kalshi_event_ticker": event_ticker,
            "polymarket_slug": slug,
            "reason": f"No Kalshi date window aligns with Poly slug date. K subs: {[km['title'] for km in kalshi_markets]}",
        })

    return matches, rejects


async def process_multi_outcome(candidate: dict) -> tuple[list[dict], list[dict]]:
    matches, rejects = [], []
    slug = candidate["polymarket"]["slug"]
    kalshi_markets = candidate["kalshi_markets"]
    event_ticker = candidate["kalshi_event"]["event_ticker"]
    k_title = candidate["kalshi_event"]["title"]
    p_question = candidate["polymarket"]["question"]

    # Extract the person/company/outcome name from the Poly slug
    slug_name = extract_name_from_slug(slug)
    if not slug_name:
        rejects.append({
            "kalshi_event_ticker": event_ticker,
            "polymarket_slug": slug,
            "reason": f"Could not extract outcome name from slug: {slug}",
        })
        return matches, rejects

    # Try slug-based matching first
    for km in kalshi_markets:
        km_title = km.get("title", "")
        if slug_name_matches_kalshi_title(slug_name, km_title):
            matches.append({
                "id": f"{slug}-{event_ticker.lower()}",
                "kalshi_ticker": km["ticker"],
                "polymarket_slug": slug,
                "direction": "kalshi_yes_eq_poly_yes",
                "notes": f"Multi-outcome: Kalshi sub '{km_title}' ↔ Poly slug '{slug_name}'. K event: {k_title}. P: {p_question}",
            })
            return matches, rejects

    # Also try Jaccard on question text as fallback
    p_lower = p_question.lower()
    p_tokens = set(p_lower.split()) - {"the", "a", "an", "of", "in", "on", "at", "to", "for", "and", "or", "is", "be", "will", "which", "who", "year", "2026", "2027", "?"}
    best_match = None
    best_score = 0.0

    for km in kalshi_markets:
        km_title = km.get("title", "").lower()
        km_tokens = set(km_title.split()) - {"the", "a", "an", "of", "in", "on", "at", "to", "for", "and", "or", "is", "be", "will"}
        if not km_tokens or not p_tokens:
            continue
        score = len(km_tokens & p_tokens) / len(km_tokens | p_tokens)
        if score > best_score:
            best_score = score
            best_match = km

    if best_match and best_score >= 0.3:
        matches.append({
            "id": f"{slug}-{event_ticker.lower()}",
            "kalshi_ticker": best_match["ticker"],
            "polymarket_slug": slug,
            "direction": "kalshi_yes_eq_poly_yes",
            "notes": f"Multi-outcome: Kalshi sub '{best_match['title']}' ↔ Poly (Jaccard={best_score:.2f}). K event: {k_title}. P: {p_question}",
        })
    else:
        rejects.append({
            "kalshi_event_ticker": event_ticker,
            "polymarket_slug": slug,
            "reason": f"No matching Kalshi sub-market for slug name '{slug_name}' (Jaccard={best_score:.2f}). K subs: {[km['title'] for km in kalshi_markets[:5]]}...",
        })

    return matches, rejects


async def process_political(candidate: dict) -> tuple[list[dict], list[dict]]:
    matches, rejects = [], []
    slug = candidate["polymarket"]["slug"]
    kalshi_markets = candidate["kalshi_markets"]
    event_ticker = candidate["kalshi_event"]["event_ticker"]
    k_title = candidate["kalshi_event"]["title"]
    p_question = candidate["polymarket"]["question"]

    # Check for primary vs general mismatch
    if is_primary_mismatch(candidate):
        rejects.append({
            "kalshi_event_ticker": event_ticker,
            "polymarket_slug": slug,
            "reason": f"General election matched to party primary. K: {k_title}. P: {p_question}",
        })
        return matches, rejects

    # Check for year mismatch
    if "2028" in k_title and "2028" not in slug:
        rejects.append({
            "kalshi_event_ticker": event_ticker,
            "polymarket_slug": slug,
            "reason": f"Election year mismatch: Kalshi is 2028",
        })
        return matches, rejects

    # Try party-based matching from slug
    party = match_party_from_slug(slug)
    if party:
        result = find_kalshi_party_ticker(kalshi_markets, party)
        if result:
            ticker, km_title = result
            matches.append({
                "id": f"{slug}-{event_ticker.lower()}",
                "kalshi_ticker": ticker,
                "polymarket_slug": slug,
                "direction": "kalshi_yes_eq_poly_yes",
                "notes": f"Political: Kalshi '{km_title}' ↔ Poly party '{party}'. K: {k_title}. P: {p_question}",
            })
            return matches, rejects

    # Try slug-based name matching for candidate-specific markets
    slug_name = extract_name_from_slug(slug)
    if slug_name:
        for km in kalshi_markets:
            if slug_name_matches_kalshi_title(slug_name, km.get("title", "")):
                matches.append({
                    "id": f"{slug}-{event_ticker.lower()}",
                    "kalshi_ticker": km["ticker"],
                    "polymarket_slug": slug,
                    "direction": "kalshi_yes_eq_poly_yes",
                    "notes": f"Political: Kalshi '{km['title']}' ↔ Poly slug '{slug_name}'. K: {k_title}. P: {p_question}",
                })
                return matches, rejects

    # Fallback to Jaccard
    return await process_multi_outcome(candidate)


async def main() -> None:
    load_dotenv()

    candidates = json.loads(_CANDIDATES_PATH.read_text())
    existing = json.loads(_MATCHES_PATH.read_text())
    existing_slugs = {m["polymarket_slug"] for m in existing}
    existing_ids = {m["id"] for m in existing}

    unmatched = [c for c in candidates if c["polymarket"]["slug"] not in existing_slugs]
    print(f"{len(unmatched)} unmatched candidates to review\n")

    new_matches: list[dict] = []
    new_rejects: list[dict] = []

    async with httpx.AsyncClient() as client:
        for c in unmatched:
            series = c["kalshi_event"]["series_ticker"]
            slug = c["polymarket"]["slug"]
            event_ticker = c["kalshi_event"]["event_ticker"]

            # 1. Blanket false positives
            if series in FALSE_POSITIVE_SERIES:
                new_rejects.append({
                    "kalshi_event_ticker": event_ticker,
                    "polymarket_slug": slug,
                    "reason": FALSE_POSITIVE_SERIES[series],
                })
                continue

            if series in FALSE_POSITIVE_SLUGS:
                new_rejects.append({
                    "kalshi_event_ticker": event_ticker,
                    "polymarket_slug": slug,
                    "reason": FALSE_POSITIVE_SLUGS[series],
                })
                continue

            if series in WEATHER_FALSE_POSITIVE_SERIES:
                new_rejects.append({
                    "kalshi_event_ticker": event_ticker,
                    "polymarket_slug": slug,
                    "reason": "Weather: different city, date, or metric between platforms",
                })
                continue

            # 2. Sports moneyline
            if series in SPORT_MONEYLINE_SERIES:
                m, r = await process_sport_moneyline(c, client)
                for match in m:
                    if match["id"] not in existing_ids:
                        new_matches.append(match)
                        existing_ids.add(match["id"])
                new_rejects.extend(r)
                continue

            # 3. MLB F5
            if series in F5_SERIES:
                m, r = await process_mlb_f5(c, client)
                for match in m:
                    if match["id"] not in existing_ids:
                        new_matches.append(match)
                        existing_ids.add(match["id"])
                new_rejects.extend(r)
                continue

            # 4. Political elections
            if series in POLITICAL_SERIES:
                m, r = await process_political(c)
                for match in m:
                    if match["id"] not in existing_ids:
                        new_matches.append(match)
                        existing_ids.add(match["id"])
                new_rejects.extend(r)
                continue

            # 5. Date-bucketed
            if series in DATE_BUCKETED_SERIES:
                m, r = await process_date_bucketed(c)
                for match in m:
                    if match["id"] not in existing_ids:
                        new_matches.append(match)
                        existing_ids.add(match["id"])
                new_rejects.extend(r)
                continue

            # 6. Multi-outcome
            if series in MULTI_OUTCOME_SERIES:
                if series == "KXATP1RANK":
                    p_q = c["polymarket"]["question"].lower()
                    if "women" in p_q or "wta" in p_q:
                        new_rejects.append({
                            "kalshi_event_ticker": event_ticker,
                            "polymarket_slug": slug,
                            "reason": "ATP men's #1 matched to women's tennis — different category",
                        })
                        continue

                m, r = await process_multi_outcome(c)
                for match in m:
                    if match["id"] not in existing_ids:
                        new_matches.append(match)
                        existing_ids.add(match["id"])
                new_rejects.extend(r)
                continue

            # 7. Uncategorized
            print(f"UNCATEGORIZED: {series} | {event_ticker} | {slug}")
            new_rejects.append({
                "kalshi_event_ticker": event_ticker,
                "polymarket_slug": slug,
                "reason": f"Uncategorized series {series} — needs manual review",
            })

    # Summary
    print(f"\n--- Results ---")
    print(f"New matches: {len(new_matches)}")
    print(f"New rejections: {len(new_rejects)}")

    # Show new matches by type
    from collections import Counter
    match_types = Counter()
    for m in new_matches:
        notes = m.get("notes", "")
        if "F5" in notes:
            match_types["MLB F5"] += 1
        elif "Date-bucketed" in notes:
            match_types["Date-bucketed"] += 1
        elif "Multi-outcome" in notes:
            match_types["Multi-outcome"] += 1
        elif "Political" in notes:
            match_types["Political"] += 1
        else:
            match_types["Sports moneyline"] += 1

    for t, count in match_types.most_common():
        print(f"  {t}: {count}")

    reject_reasons = Counter()
    for r in new_rejects:
        reason = r["reason"].split(".")[0].split("—")[0].strip()[:60]
        reject_reasons[reason] += 1
    print(f"\nRejection breakdown:")
    for reason, count in reject_reasons.most_common():
        print(f"  {reason}: {count}")

    # Write
    all_matches = existing + new_matches
    _MATCHES_PATH.write_text(json.dumps(all_matches, indent=2))
    print(f"\nWrote {len(all_matches)} total matches ({len(existing)} existing + {len(new_matches)} new)")

    _REJECTED_PATH.write_text(json.dumps(new_rejects, indent=2))
    print(f"Wrote {len(new_rejects)} rejections (replaced old file)")


if __name__ == "__main__":
    asyncio.run(main())
