import os
import json
import unicodedata

BASE_DIR = os.path.dirname(__file__)
CAPACITY_FILE = os.path.join(BASE_DIR, "capacity.json")
CARDS_FILE = os.path.join(BASE_DIR, "cards.json")
FIXTURES_FILE = os.path.join(BASE_DIR, "fixtures_cache.json")
OUTPUT_FILE = os.path.join(BASE_DIR, "capacity_cards_relation.json")


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def normalize_team_name(name: str) -> str:
    if not name:
        return ""

    name = name.strip().lower()

    replacements = {
        "ä": "a",
        "ö": "o",
        "ü": "u",
        "ß": "ss",
        ".": "",
        "-": " ",
    }

    for old, new in replacements.items():
        name = name.replace(old, new)

    # убираем акценты/диакритику на всякий случай
    name = unicodedata.normalize("NFKD", name)
    name = "".join(ch for ch in name if not unicodedata.combining(ch))

    # схлопываем пробелы
    name = " ".join(name.split())
    return name


def main():
    capacity_data = load_json(CAPACITY_FILE)
    cards_data = load_json(CARDS_FILE)
    fixtures_data = load_json(FIXTURES_FILE)

    # 1. capacity lookup по имени команды
    capacity_lookup = {}
    for venue in capacity_data.get("venues", []):
        team_name = venue.get("team_name")
        key = normalize_team_name(team_name)
        if key:
            capacity_lookup[key] = venue

    # 2. fixture lookup по fixture_id
    fixture_lookup = {}
    for fx in fixtures_data.get("response", []):
        fixture = fx.get("fixture") or {}
        fixture_id = fixture.get("id")
        if fixture_id is not None:
            fixture_lookup[fixture_id] = fx

    combined = []
    skipped_missing_fixture = 0
    skipped_missing_team = 0
    skipped_missing_capacity = 0

    unmatched_teams = {}

    for match in cards_data.get("matches", []):
        fixture_id = match.get("fixture_id")
        fx = fixture_lookup.get(fixture_id)

        if not fx:
            skipped_missing_fixture += 1
            continue

        teams = fx.get("teams") or {}
        home_team = teams.get("home") or {}
        home_team_name = home_team.get("name")

        if not home_team_name:
            skipped_missing_team += 1
            continue

        team_key = normalize_team_name(home_team_name)
        venue_info = capacity_lookup.get(team_key)

        if not venue_info:
            skipped_missing_capacity += 1
            unmatched_teams[home_team_name] = unmatched_teams.get(home_team_name, 0) + 1
            continue

        capacity = venue_info.get("capacity")
        if capacity is None:
            skipped_missing_capacity += 1
            unmatched_teams[home_team_name] = unmatched_teams.get(home_team_name, 0) + 1
            continue

        fixture = fx.get("fixture") or {}
        venue = fixture.get("venue") or {}

        combined.append(
            {
                "fixture_id": fixture_id,
                "date": match.get("date") or fixture.get("date"),
                "home_team_name": home_team_name,
                "away_team_name": (teams.get("away") or {}).get("name"),
                "fixture_venue_id": match.get("venue_id"),
                "fixture_venue_name": venue.get("name"),
                "fixture_city": venue.get("city"),
                "team_capacity_venue_id": venue_info.get("venue_id"),
                "team_capacity_venue_name": venue_info.get("name"),
                "team_capacity_city": venue_info.get("city"),
                "capacity": capacity,
                "match": match.get("match"),
                "yellow_home": match.get("yellow_home"),
                "red_home": match.get("red_home"),
                "yellow_away": match.get("yellow_away"),
                "red_away": match.get("red_away"),
                "yellow_total": match.get("yellow_total"),
                "red_total": match.get("red_total"),
                "cards_total": match.get("cards_total"),
            }
        )

    out = {
        "_meta": {
            "records": len(combined),
            "skipped_missing_fixture": skipped_missing_fixture,
            "skipped_missing_team": skipped_missing_team,
            "skipped_missing_capacity": skipped_missing_capacity,
            "capacity_source": "capacity.json via team_name from /teams",
            "match_bridge_source": "fixtures_cache.json via fixture_id",
        },
        "unmatched_home_teams": dict(sorted(unmatched_teams.items())),
        "matches": combined,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"Saved {OUTPUT_FILE}")
    print(f"Used matches: {len(combined)}")
    print(f"Skipped because fixture missing: {skipped_missing_fixture}")
    print(f"Skipped because home team missing: {skipped_missing_team}")
    print(f"Skipped because capacity missing: {skipped_missing_capacity}")

    if unmatched_teams:
        print("\nUnmatched home teams:")
        for team_name, count in sorted(unmatched_teams.items()):
            print(f"  {team_name}: {count}")


if __name__ == "__main__":
    main()