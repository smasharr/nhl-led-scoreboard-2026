NHL LED Scoreboard 2026

A Raspberry Pi–powered NHL scoreboard using a 64x32 HUB75 LED matrix.

This project displays live NHL scores with team colors and logos and includes support for a favorite team hype screen.


WHAT THIS IS

This is a Python project designed to run on a Raspberry Pi connected to a HUB75 LED matrix.
It pulls live NHL game data from the public NHL API and displays it on the LED panel.

No accounts, no paid APIs, no cloud services.


FEATURES

- Live NHL scores
- Team-colored abbreviations and logos
- Favorite team support
- Hype screen between score cycles
- Designed for continuous operation on a Raspberry Pi


DEMO VIDEO

Watch the NHL LED Scoreboard in action:
https://github.com/smasharr/nhl-led-scoreboard-2026/releases/download/v1.0/IMG_4164.mov


HARDWARE

- Raspberry Pi (3, 4, or newer recommended)
- 64x32 HUB75 LED matrix
- RGB Matrix HAT (Adafruit or compatible)
- External 5V power supply for the LED panel

Do NOT power the LED matrix from the Raspberry Pi alone.


HOW IT WORKS

The main script:
- Fetches live NHL data
- Formats scores and team info
- Renders everything to the LED matrix using the rgbmatrix library

All rendering happens locally on the Pi.


FAVORITE TEAM CONFIGURATION

A file named "favorite_team.txt" is used to store the user’s favorite team.

An example file is included:
favorite_team.txt.example

Copy it and set your favorite team using a valid NHL abbreviation (for example: STL).

QUICK START – FIRST TIME SETUP

This section assumes a fresh Raspberry Pi.

1) Install Raspberry Pi OS
	•	Flash Raspberry Pi OS (Lite or Desktop) to a micro-SD card using Raspberry Pi Imager.
	•	Insert SD card into the Pi and power it on.
	•	Complete the initial Raspberry Pi setup.

2) Connect to WiFi
If using a monitor and keyboard:
	•	Select your WiFi network during the Raspberry Pi OS setup.

If setting up headless (no monitor):

Before first boot, place this file on the SD card boot partition:

wpa_supplicant.conf
country=US
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1

network={
    ssid="YOUR_WIFI_NAME"
    psk="YOUR_WIFI_PASSWORD"
}

On first boot, the Pi will automatically connect to WiFi.

⸻

3) Download the Scoreboard Project
Open a terminal on the Pi and run:
git clone https://github.com/smasharr/nhl-led-scoreboard-2026.git
cd nhl-led-scoreboard-2026

4) Install Dependencies
pip install -r requirements.txt

RUNNING THE SCOREBOARD

The main entry point is:
nhl_scoreboard_led.py

This script must be run with sudo to access GPIO hardware.

Example command:
sudo python3 nhl_scoreboard_led.py

Make sure this works before proceeding to automatic startup.


PROJECT STRUCTURE

.
├── nhl_scoreboard_led.py
├── nhl_scoreboard.py
├── favorite_team.txt.example
├── assets/
│   └── logos/
├── systemd/
│   └── nhl-scoreboard.service
└── .gitignore


NOTES

- Uses the public NHL API
- Not affiliated with or endorsed by the NHL
- LED flicker and brightness depend on panel quality, wiring, and power


RUN ON BOOT (OPTIONAL – SYSTEMD)

This step is optional and should only be completed after confirming the scoreboard runs correctly when launched manually.

From the Raspberry Pi, inside the project directory:

sudo cp systemd/nhl-scoreboard.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable nhl-scoreboard.service
sudo systemctl start nhl-scoreboard.service

To check status:
systemctl status nhl-scoreboard.service


AUTHOR

Created by @smasharr
AI-assisted development.


LICENSE

MIT License
