import requests
import sys

TEAM_ABBREV = "STL"
URL = "https://api-web.nhle.com/v1/score/now"

def iter_games(data):
    if isinstance(data.get("games"), list):
        for g in data["games"]:
            yield g
        return
    if isinstance(data.get("gamesByDate"), list):
        for day in data["gamesByDate"]:
            for g in day.get("games", []):
                yield g
        return

def main():
    r = requests.get(URL, timeout=10)
    r.raise_for_status()
    data = r.json()

    for g in iter_games(data):
        home = g.get("homeTeam", {})
        away = g.get("awayTeam", {})

        home_ab = (home.get("abbrev") or home.get("triCode") or "").upper()
        away_ab = (away.get("abbrev") or away.get("triCode") or "").upper()

        if TEAM_ABBREV not in (home_ab, away_ab):
            continue

        home_name = home.get("name", {}).get("default", home_ab)
        away_name = away.get("name", {}).get("default", away_ab)

        hs = home.get("score", 0)
        a_s = away.get("score", 0)

        state = g.get("gameState", "")
        time_rem = (g.get("clock") or {}).get("timeRemaining", "")
        period = (g.get("periodDescriptor") or {}).get("number", "")

        print(f"{away_name} {a_s} @ {home_name} {hs} | {state} P{period} {time_rem}")
        sys.exit(0)

    print("No Blues game right now.")

if __name__ == "__main__":
    main()
