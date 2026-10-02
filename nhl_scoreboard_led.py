#!/usr/bin/env python3
import time
import signal
import sys
import json
import random
import requests
import re
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics
from PIL import Image
import os

SCORE_TMPL = "https://api-web.nhle.com/v1/score/{DATE}"
GAME_DAY_ROLLOVER_HOUR = 4

# Favorite team config
FAVORITE_TEAM_FILE = "/home/pi/scoreboard/favorite_team.txt"
SCHED_TMPL = "https://api-web.nhle.com/v1/club-schedule/{TEAM}/week/{DATE}"
LOGO_DIR = "/home/pi/scoreboard/assets/logos"
FALLBACK_LOGO_PATH = "/home/pi/scoreboard/assets/blues_logo.png"

SECONDS_PER_GAME = 4
REFRESH_SECONDS = 30
DISPLAY_WIDTH = 64
DISPLAY_HEIGHT = 32
NEXT_GAME_SECONDS = SECONDS_PER_GAME + 2

def get_favorite_team():
    try:
        with open(FAVORITE_TEAM_FILE, "r") as f:
            t = f.read().strip().upper()
            if len(t) == 3:
                return t
    except:
        pass
    return "STL"


TIMEZONE_FILE = "/home/pi/scoreboard/timezone.txt"

def get_timezone():
    try:
        with open(TIMEZONE_FILE) as f:
            return ZoneInfo(f.read().strip())
    except (OSError, ValueError, KeyError):
        return ZoneInfo("America/Chicago")

def get_display_date(now=None):
    """Keep the previous calendar day's games until 4 AM in the chosen zone."""
    local = (now or datetime.now(timezone.utc)).astimezone(get_timezone())
    day = local.date()
    if local.hour < GAME_DAY_ROLLOVER_HOUR:
        day -= timedelta(days=1)
    return day.isoformat()


# ---------- colors ----------
YELLOW = graphics.Color(255, 215, 0)
WHITE = graphics.Color(255, 255, 255)
BLACK = graphics.Color(0, 0, 0)

YELLOW_RGB = (255, 215, 0)

TEAM_COLORS = {
    "ANA": (252, 76, 2), "ARI": (140, 38, 51), "UTA": (100, 180, 240),
    "BOS": (252, 181, 20), "BUF": (0, 38, 84), "CGY": (200, 16, 46),
    "CAR": (206, 17, 38), "CHI": (207, 10, 44), "COL": (111, 38, 61),
    "CBJ": (0, 38, 84), "DAL": (0, 104, 71), "DET": (206, 17, 38),
    "EDM": (4, 30, 66), "FLA": (200, 16, 46), "LAK": (17, 17, 17),
    "MIN": (2, 73, 48), "MTL": (175, 30, 45), "NSH": (255, 184, 28),
    "NJD": (206, 17, 38), "NYI": (0, 83, 155), "NYR": (0, 56, 168),
    "OTT": (200, 16, 46), "PHI": (247, 73, 2), "PIT": (252, 181, 20),
    "SEA": (0, 22, 40), "SJS": (0, 109, 117), "STL": (0, 80, 255),
    "TBL": (0, 40, 104), "TOR": (0, 32, 91), "VAN": (0, 32, 91),
    "VGK": (185, 151, 91), "WSH": (200, 16, 46), "WPG": (0, 32, 91),
}

TEAM_CONFETTI = {
    "NYR": ((0, 56, 168), (206, 17, 38)),
    "STL": ((0, 80, 255), (255, 215, 0)),
    "TOR": ((0, 32, 91), (255, 255, 255)),
    "TBL": ((0, 40, 104), (255, 255, 255)),
    "VAN": ((0, 32, 91), (0, 104, 71)),
    "SEA": ((0, 22, 40), (0, 109, 117)),
    "EDM": ((4, 30, 66), (252, 76, 2)),
    "BUF": ((0, 38, 84), (252, 181, 20)),
    "NSH": ((255, 184, 28), (0, 40, 104)),
    "VGK": ((185, 151, 91), (17, 17, 17)),
    "LAK": ((17, 17, 17), (255, 255, 255)),
}

TEAM_NAMES = {
    "ANA": "DUCKS",
    "ARI": "COYOTES",
    "UTA": "MAMMOTH",
    "BOS": "BRUINS",
    "BUF": "SABRES",
    "CAR": "HURRICANES",
    "CBJ": "BLUE JACKETS",
    "CGY": "FLAMES",
    "CHI": "BLACKHAWKS",
    "COL": "AVALANCHE",
    "DAL": "STARS",
    "DET": "RED WINGS",
    "EDM": "OILERS",
    "FLA": "PANTHERS",
    "LAK": "KINGS",
    "MIN": "WILD",
    "MTL": "CANADIENS",
    "NJD": "DEVILS",
    "NSH": "PREDATORS",
    "NYI": "ISLANDERS",
    "NYR": "RANGERS",
    "OTT": "SENATORS",
    "PHI": "FLYERS",
    "PIT": "PENGUINS",
    "SEA": "KRAKEN",
    "SJS": "SHARKS",
    "STL": "BLUES",
    "TBL": "LIGHTNING",
    "TOR": "MAPLE LEAFS",
    "VAN": "CANUCKS",
    "VGK": "GOLDEN KNIGHTS",
    "WSH": "CAPITALS",
    "WPG": "JETS",
}

def team_color(abbrev):
    r, g, b = TEAM_COLORS.get((abbrev or "").upper(), (255, 255, 255))
    return graphics.Color(r, g, b)

def team_rgb(abbrev):
    return TEAM_COLORS.get((abbrev or "").upper(), (255, 255, 255))

# ---------- fonts ----------
font = graphics.Font()
for fp in [
    "/home/pi/rpi-rgb-led-matrix/fonts/5x7.bdf",
    "/home/pi/rpi-rgb-led-matrix/fonts/6x10.bdf",
    "/home/pi/rpi-rgb-led-matrix/fonts/6x9.bdf",
    "/home/pi/rpi-rgb-led-matrix/fonts/6x12.bdf",
]:
    try:
        font.LoadFont(fp)
        break
    except:
        pass

small_font = graphics.Font()
try:
    small_font.LoadFont("/home/pi/rpi-rgb-led-matrix/fonts/4x6.bdf")
except:
    small_font.LoadFont("/home/pi/rpi-rgb-led-matrix/fonts/5x7.bdf")

# ---------- matrix ----------
options = RGBMatrixOptions()
options.rows = 32
options.cols = 64
options.chain_length = 1
options.parallel = 1
options.brightness = 80
options.gpio_slowdown = 3
# ===== LED PANEL FLICKER STABILIZATION SETTINGS (FINAL) =====
options.hardware_mapping = "adafruit-hat"
options.panel_type = "FM6126A"
options.pwm_dither_bits = 0
options.pwm_lsb_nanoseconds = 300
options.limit_refresh_rate_hz = 120
matrix = RGBMatrix(options=options)
canvas = matrix.CreateFrameCanvas()

def swap():
    global canvas
    canvas = matrix.SwapOnVSync(canvas)

# ---------- helpers ----------
def iter_games(data):
    if "games" in data:
        yield from data["games"]
    elif "gamesByDate" in data:
        for d in data["gamesByDate"]:
            yield from d.get("games", [])

def abbrev(team):
    return (team.get("abbrev") or team.get("triCode") or "???").upper()

def parse_start_time(g):
    for key in ("startTimeUTC", "gameStartTimeUTC", "startTime"):
        ts = g.get(key)
        if ts:
            try:
                cst = get_timezone()
                return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(cst).strftime("%-I:%M %p")
            except:
                pass
    return ""

def parse_start_dt_utc(g):
    for key in ("startTimeUTC", "gameStartTimeUTC", "startTime"):
        ts = g.get(key)
        if ts:
            try:
                return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(timezone.utc)
            except:
                pass
    return None

def convert_status_to_cst(status):
    """Convert ESPN status string with date/time from EST to CST"""
    # Match pattern like "2/14 - 3:10 PM EST"
    match = re.search(r'(\d{1,2}/\d{1,2})\s*-?\s*(\d{1,2}):(\d{2})\s*(AM|PM)\s*EST', status)
    if match:
        date_part = match.group(1)
        hour = int(match.group(2))
        minute = int(match.group(3))
        ampm = match.group(4)

        # Convert to 24-hour format
        if ampm == "PM" and hour != 12:
            hour += 12
        elif ampm == "AM" and hour == 12:
            hour = 0

        # Subtract 1 hour to go from EST to CST
        hour -= 1
        if hour < 0:
            hour = 23
            ampm = "PM"
        elif hour == 0:
            hour = 12
            ampm = "AM"
        elif hour < 12:
            ampm = "AM"
        elif hour == 12:
            ampm = "PM"
        else:
            hour -= 12
            ampm = "PM"

        # Return the converted time without EST label
        return f"{date_part} {hour}:{minute:02d}"

    return status

def text_width(s, fnt):
    return sum(fnt.CharacterWidth(ord(c)) for c in s)

def fit_text(s, fnt, max_w):
    while s and text_width(s, fnt) > max_w:
        s = s[:-1]
    return s

def score_line(a, as_, h, hs):
    for s in (
        f"{a}{as_} @ {h}{hs}",
        f"{a}{as_}@{h}{hs}",
        f"{a}{as_}-{h}{hs}",
    ):
        if text_width(s, font) <= DISPLAY_WIDTH:
            return s
    return fit_text(f"{a}{as_} @ {h}{hs}", font, DISPLAY_WIDTH)

def game_key(g):
    gid = g.get("id") or g.get("gameId")
    if gid:
        return str(gid)
    home = abbrev(g.get("homeTeam", {}))
    away = abbrev(g.get("awayTeam", {}))
    return f"{away}@{home}"

# ---------- score change tracking ----------
SCORES_FILE = "/home/pi/scoreboard/last_scores.json"

def load_scores():
    try:
        with open(SCORES_FILE) as f:
            return {k: tuple(v) for k, v in json.load(f).items()}
    except:
        return {}

def save_scores():
    try:
        with open(SCORES_FILE, "w") as f:
            json.dump(last_scores, f)
    except:
        pass

last_scores = load_scores()
flash_once = set()

# ---------- screens ----------
def draw_centered(l1, l2, c1, c2):
    canvas.Clear()
    graphics.DrawText(canvas, font, max((DISPLAY_WIDTH - text_width(l1, font)) // 2, 0), 12, c1, l1)
    graphics.DrawText(canvas, font, max((DISPLAY_WIDTH - text_width(l2, font)) // 2, 0), 28, c2, l2)
    swap()

def draw_game(g):
    k = game_key(g)
    should_flash = k in flash_once
    if should_flash:
        flash_once.discard(k)

    home = g.get("homeTeam", {})
    away = g.get("awayTeam", {})
    ha = abbrev(home)
    aa = abbrev(away)
    hs = home.get("score", 0)
    as_ = away.get("score", 0)

    l1 = score_line(aa, as_, ha, hs)

    state = (g.get("gameState") or "").upper()
    clock = g.get("clock", {}) or {}
    period = (g.get("periodDescriptor", {}) or {}).get("number", "")
    time_rem = (clock.get("timeRemaining") or "").strip()

    if state == "LIVE" and period and time_rem:
        l2 = f"P{period} {time_rem}"
    elif state in ("PRE", "FUT"):
        l2 = parse_start_time(g)
    else:
        l2 = "FINAL"

    c = team_color(ha)

    if should_flash:
        for _ in range(3):
            draw_centered(l1, fit_text(l2, font, DISPLAY_WIDTH), WHITE, WHITE)
            time.sleep(0.10)
            draw_centered(l1, fit_text(l2, font, DISPLAY_WIDTH), BLACK, BLACK)
            time.sleep(0.06)

    draw_centered(l1, fit_text(l2, font, DISPLAY_WIDTH), c, c)

def hype_screen_scroll():
    team = get_favorite_team()
    team_col = team_color(team)
    team_name = TEAM_NAMES.get(team, team)

    top = "LETS GO"
    bottom = f"{team_name}!!!!"

    top_x = max((DISPLAY_WIDTH - text_width(top, font)) // 2, 0)
    bottom_w = text_width(bottom, font)

    for x in range(DISPLAY_WIDTH, -bottom_w - 1, -1):
        canvas.Clear()
        graphics.DrawText(canvas, font, top_x, 12, team_col, top)
        graphics.DrawText(canvas, font, x, 28, team_col, bottom)
        swap()
        time.sleep(0.05)

def confetti(duration=0.9):
    fav = get_favorite_team()
    primary, secondary = TEAM_CONFETTI.get(fav, (team_rgb(fav), YELLOW_RGB))

    end = time.time() + duration
    while time.time() < end:
        canvas.Clear()

        for _ in range(85):
            canvas.SetPixel(
                random.randrange(DISPLAY_WIDTH),
                random.randrange(DISPLAY_HEIGHT),
                *primary
            )
        for _ in range(25):
            canvas.SetPixel(
                random.randrange(DISPLAY_WIDTH),
                random.randrange(DISPLAY_HEIGHT),
                *secondary
            )

        swap()
        time.sleep(0.06)

def surprise_screen():
    confetti()

# ---------- Next Game ----------
_logo_cache_team = None
LOGO = None
LOGO_W, LOGO_H = 32, 26

def load_logo_for(team):
    path = f"{LOGO_DIR}/{team}.png"
    use_path = path if os.path.exists(path) else FALLBACK_LOGO_PATH
    try:
        img = Image.open(use_path).convert("RGBA")
        img = img.resize((LOGO_W, LOGO_H), Image.NEAREST)
        rgb_img = img.convert("RGB")
        return rgb_img
    except Exception as e:
        return None

def draw_logo(img, x, y):
    if not img:
        return
    for ix in range(img.width):
        for iy in range(img.height):
            r, g, b = img.getpixel((ix, iy))
            canvas.SetPixel(x + ix, y + iy, r, g, b)

def fetch_fav_next_game(team):
    try:
        data = requests.get(SCHED_TMPL.format(TEAM=team, DATE=get_display_date()), timeout=10).json()
        now_utc = datetime.now(timezone.utc)
        future = []
        for gg in iter_games(data):
            dt = parse_start_dt_utc(gg)
            if dt and dt > now_utc:
                future.append((dt, gg))
        if future:
            future.sort(key=lambda x: x[0])
            return future[0][1]
    except:
        pass
    return None

def fav_next_game_screen(team, g):
    global _logo_cache_team, LOGO
    if _logo_cache_team != team or LOGO is None:
        LOGO = load_logo_for(team)
        _logo_cache_team = team

    canvas.Clear()
    ly = (DISPLAY_HEIGHT - LOGO_H) // 2
    if LOGO:
        draw_logo(LOGO, 0, ly)

    tx = LOGO_W + 2
    avail = DISPLAY_WIDTH - tx

    graphics.DrawText(canvas, small_font, tx, 7, WHITE, "NEXT")
    graphics.DrawText(canvas, small_font, tx, 14, WHITE, "GAME")

    if not g:
        graphics.DrawText(canvas, small_font, tx, 26, WHITE, "TBD")
        swap()
        time.sleep(NEXT_GAME_SECONDS)
        return

    home = g.get("homeTeam", {})
    away = g.get("awayTeam", {})
    opp_team = away if abbrev(home) == team else home
    opp = abbrev(opp_team)

    r, gg, b = TEAM_COLORS.get(opp, (255, 255, 255))
    opp_color = graphics.Color(r, gg, b)

    dt = parse_start_dt_utc(g)
    local = dt.astimezone(get_timezone()) if dt else None

    # Show date and time in CST
    if local:
        cst = get_timezone()
        local_cst = local.astimezone(cst)
        when = local_cst.strftime("%a")[0:2] + " " + local_cst.strftime("%-I:%M")
    else:
        when = ""

    graphics.DrawText(canvas, small_font, tx, 21, opp_color, fit_text(f"vs {opp}", small_font, avail))
    graphics.DrawText(canvas, small_font, tx, 28, WHITE, when)

    swap()
    time.sleep(NEXT_GAME_SECONDS)

def claude_was_here_screen():
    claude_orange = graphics.Color(217, 90, 40)
    draw_centered("CLAUDE CODE", "WAS HERE", claude_orange, claude_orange)
    time.sleep(3)

def handle_shutdown(sig, frame):
    matrix.Clear()
    sys.exit(0)

signal.signal(signal.SIGTERM, handle_shutdown)
signal.signal(signal.SIGINT, handle_shutdown)

# ---------- main ----------
def fetch_games(display_date=None):
    try:
        day = display_date or get_display_date()
        response = requests.get(SCORE_TMPL.format(DATE=day), timeout=10)
        response.raise_for_status()
        data = response.json()
        if not isinstance(data.get("games"), list):
            raise ValueError("Missing games list in NHL response")
        return data["games"]
    except Exception as exc:
        print(f"NHL score refresh failed: {exc}", flush=True)
        return None


def fetch_display_games(day):
    # Also recover an exceptionally late live game after a restart past 4 AM.
    previous = (datetime.fromisoformat(day).date() - timedelta(days=1)).isoformat()
    prior_games = fetch_games(previous)
    if prior_games is None:
        return None
    if any(g.get("gameState") in ("LIVE", "CRIT") for g in prior_games):
        print(f"Keeping {previous}: games still live", flush=True)
        return prior_games
    return fetch_games(day)


def main():
    games = []
    last_fetch = 0
    fetched_day = None
    attempted_day = None
    idx = 0

    fav_next = None
    last_fav_fetch = 0
    fav_cached = None

    while True:
        now = time.time()

        display_day = get_display_date()
        if attempted_day != display_day or (now - last_fetch) > REFRESH_SECONDS:
            new = fetch_display_games(display_day)
            last_fetch = now
            attempted_day = display_day
            if fetched_day != display_day:
                fav_next = None
                last_fav_fetch = 0
            if new is not None:
                for g in new:
                    home = g.get("homeTeam", {})
                    away = g.get("awayTeam", {})
                    hs = home.get("score", 0)
                    as_ = away.get("score", 0)

                    k = game_key(g)
                    prev = last_scores.get(k)
                    curr = (as_, hs)

                    if prev is not None and prev != curr:
                        flash_once.add(k)

                    last_scores[k] = curr
                save_scores()

                games = new
                if fetched_day != display_day:
                    idx = 0
                    print(f"NHL display day: {display_day} ({get_timezone()})", flush=True)
                fetched_day = display_day

        fav = get_favorite_team()
        if fav_cached != fav:
            fav_cached = fav
            fav_next = None
            last_fav_fetch = 0

        if fav_next is None or (now - last_fav_fetch) > 900:
            fav_next = fetch_fav_next_game(fav_cached)
            last_fav_fetch = now

        if not games:
            draw_centered("NO NHL", "GAMES", WHITE, WHITE)
            time.sleep(2)
            continue

        n = len(games)

        if idx % n == 0:
            claude_was_here_screen()
            fav_next_game_screen(fav_cached, fav_next)

        draw_game(games[idx % n])
        idx += 1
        time.sleep(SECONDS_PER_GAME)

        if idx % n == 0:
            hype_screen_scroll()
            surprise_screen()

if __name__ == "__main__":
    main()
