import os
import json

BASE_DIR = os.path.dirname(__file__)
CAPACITY_FILE = os.path.join(BASE_DIR, "capacity.json")
CARDS_FILE = os.path.join(BASE_DIR, "cards.json")
OUTPUT_FILE = os.path.join(BASE_DIR, "capacity_cards_relation.json")


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)



def main():
    capacity_data = load_json(CAPACITY_FILE)
    cards_data = load_json(CARDS_FILE)

    capacity_lookup = {}
    for venue in capacity_data.get("venues", []):
        venue_id = venue.get("venue_id")
        if venue_id is not None:
            capacity_lookup[venue_id] = venue

    combined = []
    skipped_missing_venue = 0
    skipped_missing_capacity = 0

    for match in cards_data.get("matches", []):
        venue_id = match.get("venue_id")
        venue_info = capacity_lookup.get(venue_id)

        if not venue_info:
            skipped_missing_venue += 1
            continue

        capacity = venue_info.get("capacity")
        if capacity is None:
            skipped_missing_capacity += 1
            continue

        combined.append(
            {
                "fixture_id": match.get("fixture_id"),
                "date": match.get("date"),
                "venue_id": venue_id,
                "venue_name": venue_info.get("name"),
                "city": venue_info.get("city"),
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
            "skipped_missing_venue": skipped_missing_venue,
            "skipped_missing_capacity": skipped_missing_capacity,
        },
        "matches": combined,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"Saved {OUTPUT_FILE}")
    print(f"Used matches: {len(combined)}")
    print(f"Skipped because venue missing: {skipped_missing_venue}")
    print(f"Skipped because capacity missing: {skipped_missing_capacity}")


if __name__ == "__main__":
    main()
