# NHL LED Scoreboard

A Raspberry Pi–powered NHL scoreboard using a 64x32 HUB75 LED matrix.

This project displays live NHL scores with team colors and logos and includes support for a favorite team hype screen.

---

## What This Is

This is a Python project designed to run on a Raspberry Pi connected to a HUB75 LED matrix.  
It pulls live NHL game data from the public NHL API and displays it on the LED panel.

No accounts, no paid APIs, no cloud services.

---

## Features

- Live NHL scores
- Team-colored abbreviations and logos
- Favorite team support
- Hype screen between score cycles
- Designed for continuous operation on a Raspberry Pi

---

## Hardware

- Raspberry Pi (3, 4, or newer recommended)
- 64x32 HUB75 LED matrix
- RGB Matrix HAT (Adafruit or compatible)
- External 5V power supply for the LED panel

**Do not power the LED matrix from the Raspberry Pi alone.**

---

## How It Works

The main script:
- Fetches live NHL data
- Formats scores and team info
- Renders everything to the LED matrix using the rgbmatrix library

All rendering happens locally on the Pi.

---

## Favorite Team Configuration

A file named `favorite_team.txt` is used to store the user’s favorite team.

An example file is included:
favorite_team.txt.example

Users should copy this file and replace the contents with a valid NHL team abbreviation (for example: `STL`).

---

## Running the Scoreboard

The main entry point is:

nhl_scoreboard_led.py

This script must be run with sudo to access GPIO hardware.

---

## Project Structure

.
├── nhl_scoreboard_led.py
├── nhl_scoreboard.py
├── favorite_team.txt.example
├── assets/
│ └── logos/
└── .gitignore

---

## Notes

- Uses the public NHL API
- Not affiliated with or endorsed by the NHL
- LED flicker and brightness depend on panel quality, wiring, and power

---

## License

MIT License

---

## Author

Created by @smasharr
AI-assisted development.



