# Raspberry Pi Setup — 24/7 Bot

## What you need
- Raspberry Pi (any model with 512MB+ RAM — Pi 3/4/5 recommended)
- Raspberry Pi OS (64-bit recommended) — fresh install or existing
- Your Binance API key and secret
- The bot files on the Pi (via USB, SCP, or Git)

---

## Step 1 — Get the files onto the Pi

**Option A — Git (recommended):**
```bash
cd ~
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git Trader
cd Trader
```

**Option B — Copy from your PC over the network:**
```bash
# Run this on your PC, not the Pi
scp -r /path/to/Trader pi@raspberrypi.local:~/Trader
```

---

## Step 2 — Install Python dependencies

```bash
cd ~/Trader
pip install setuptools --break-system-packages
pip install -r requirements.txt --break-system-packages
```

If `pip` isn't found, install it first:
```bash
sudo apt update && sudo apt install python3-pip -y
```

---

## Step 3 — Create your `.env` file

```bash
cp .env.example .env
nano .env
```

Paste in your Binance API keys:
```
BINANCE_API_KEY=your_key_here
BINANCE_API_SECRET=your_secret_here
```

Save with `Ctrl+O`, exit with `Ctrl+X`.

> US users: also add `BINANCE_TLD=us` on a new line.

---

## Step 4 — Test it runs manually

```bash
cd ~/Trader
python3 run_swing.py
```

You should see startup logs and a summary table. Press `Ctrl+C` to stop after confirming it works.

---

## Step 5 — Set up as a systemd service (runs 24/7, auto-restarts)

Create the service file:
```bash
sudo nano /etc/systemd/system/trader.service
```

Paste this — **replace `pi` with your actual username** (check with `whoami`):
```ini
[Unit]
Description=Crypto Swing Trading Bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/Trader
ExecStart=/usr/bin/python3 /home/pi/Trader/run_swing.py
Restart=on-failure
RestartSec=30
StandardOutput=append:/home/pi/Trader/logs/bot.log
StandardError=append:/home/pi/Trader/logs/bot.log

[Install]
WantedBy=multi-user.target
```

Save with `Ctrl+O`, exit with `Ctrl+X`.

Make sure the logs directory exists:
```bash
mkdir -p ~/Trader/logs
```

Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable trader
sudo systemctl start trader
```

`enable` makes it start automatically on every reboot.

---

## Checking the bot

**See if it's running:**
```bash
sudo systemctl status trader
```

**Watch live logs:**
```bash
tail -f ~/Trader/logs/bot.log
```

**See recent trades:**
```bash
tail -f ~/Trader/logs/trades.log
```

---

## Stopping and restarting

```bash
# Stop
sudo systemctl stop trader

# Restart (e.g. after changing config.py)
sudo systemctl restart trader

# Disable auto-start on boot
sudo systemctl disable trader
```

---

## Updating the bot

```bash
sudo systemctl stop trader
cd ~/Trader
git pull
sudo systemctl start trader
```

---

## Keeping the Pi's clock accurate

The bot schedules trades at 00:15 UTC. Make sure time sync is on:
```bash
sudo timedatectl set-ntp true
timedatectl status
```

You should see `NTP service: active`.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `ModuleNotFoundError` | Re-run `pip install -r requirements.txt --break-system-packages` |
| `EnvironmentError: BINANCE_API_KEY missing` | Check your `.env` file exists and has real keys |
| Service won't start | Run `journalctl -u trader -n 50` to see the full error |
| Bot crashes and won't restart | Check `logs/bot.log` — likely an API error or network issue |
| Clock is wrong | Run `sudo timedatectl set-ntp true` |
