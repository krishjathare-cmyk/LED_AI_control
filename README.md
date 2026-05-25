# Screen LED Control

FastAPI-controlled Bluetooth LED ambient lighting. The script samples the screen color, applies the selected color mode, and sends RGB + brightness values to the LED device over Bluetooth.

## Files

- `Screen_led_control.py` - main FastAPI + LED controller script.
- `WhatsApp Video 2026-05-25 at 4.44.04 AM.mp4` - demo video showing the LED response.

## Run

Install dependencies:

```powershell
python -m pip install fastapi uvicorn bleak mss numpy opencv-python pydantic
```

Start the controller:

```powershell
python Screen_led_control.py
```

Open the auto-generated API docs:

```text
http://127.0.0.1:8000/docs
```

## Modes

- `screen` - use the weighted average screen color directly.
- `anime` - boost saturation/contrast for stronger animated visuals.
- `movie` - map the screen color to the closest color in the selected movie palette.

## Endpoints

### `GET /`

Checks that the API is running.

Response:

```json
{
  "message": "LED Control API is running",
  "docs": "Open http://127.0.0.1:8000/docs"
}
```

### `GET /state`

Returns the current mode, selected movie, and available options.

Example:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/state"
```

### `GET /palettes`

Returns all saved movie palettes.

Example:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/palettes"
```

### `POST /mode`

Changes the active color mode.

Body:

```json
{
  "mode": "anime"
}
```

For movie mode with an existing palette:

```json
{
  "mode": "movie",
  "movie": "harry potter goblet of fire"
}
```

PowerShell:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/mode" -Method Post -ContentType "application/json" -Body '{"mode":"anime"}'
```

### `POST /palette`

Adds or replaces a movie palette, then switches to movie mode using that palette.

Body:

```json
{
  "movie": "harry potter goblet of fire",
  "colors": [
    [18, 24, 28],
    [45, 53, 45],
    [129, 88, 44],
    [160, 118, 61],
    [96, 32, 29]
  ]
}
```

PowerShell:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/palette" -Method Post -ContentType "application/json" -Body '{"movie":"harry potter goblet of fire","colors":[[18,24,28],[45,53,45],[129,88,44],[160,118,61],[96,32,29]]}'
```

Each color must be an RGB list:

```json
[r, g, b]
```

Each value must be between `0` and `255`.

### `POST /movie`

Switches to movie mode using an existing saved palette.

Body:

```json
{
  "movie": "harry potter goblet of fire"
}
```

PowerShell:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/movie" -Method Post -ContentType "application/json" -Body '{"movie":"harry potter goblet of fire"}'
```

### `POST /bt`

Updates the Bluetooth LED address and GATT characteristic UUID while the program is running.

Body:

```json
{
  "LED_ADDRESS": "BE:68:0B:00:3A:68",
  "CHAR_UUID": "0000ee01-0000-1000-8000-00805f9b34fb"
}
```

PowerShell:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/bt" -Method Post -ContentType "application/json" -Body '{"LED_ADDRESS":"BE:68:0B:00:3A:68","CHAR_UUID":"0000ee01-0000-1000-8000-00805f9b34fb"}'
```

Note: the new Bluetooth values are kept only while the script is running. Restarting the script uses the defaults written at the top of `Screen_led_control.py`.

## Demo

The included WhatsApp video demonstrates the LED controller responding to screen changes and API-driven mode control.
