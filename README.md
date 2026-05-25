# Screen LED Control

FastAPI-controlled Bluetooth LED ambient lighting. The project samples the screen, transforms the captured color through selectable modes, and sends RGB + brightness values to an LED device over Bluetooth.

The goal is to make the LEDs behave like a lightweight visual extension of the screen. Instead of always sending raw screen colors, the controller can switch between different modes depending on the content style: direct screen matching, stronger anime-style colors, or movie-specific color palettes.

## Project Idea

The controller is built around modes. Each mode takes the same screen sample but changes how the final LED color is selected:

- `screen` mode keeps the color close to the actual screen average.
- `anime` mode increases contrast and saturation so colorful animated scenes feel stronger.
- `movie` mode limits the output to a selected movie palette, so the LEDs follow the visual identity of that film instead of showing every possible screen color.

This makes the system more flexible than a normal ambient LED setup. The API can change the mode, add new movie palettes, switch movies, and update Bluetooth settings while the program is running.

## Why Movie Palette Logic Works

Movie mode works by treating the screen color as a reference and then choosing the closest color from a fixed palette. For example, if the screen average is a dark orange and the selected movie palette contains candle amber, fire gold, lake blue, and forest green, the algorithm compares the screen color against each palette color and picks the nearest one.

This keeps the lighting inside the chosen movie's color language. The LEDs still react to what is happening on the screen, but they are constrained to colors that match the movie mood. That is useful because many films have recognizable grading, such as cold blues, warm amber highlights, muted greens, or dark red shadows.

The current version uses one average screen color, weighted toward the center of the screen. Center weighting helps because the main subject is often near the middle, so the LEDs respond more to important visual content and less to borders or UI elements.

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

## Future Updates

The next major step is per-LED control. Instead of sending one color to the whole LED strip, the screen can be divided into regions and each LED can receive a different color. This would allow moving objects on the screen to be visualized across the LEDs, making motion feel directional instead of only changing the whole strip at once.

Future versions can also improve color grading with sequence models such as GRU, RNN, or LSTM networks. These models can learn from recent frames, not just the current frame, so the lighting can become smoother and more cinematic. A model could learn when to keep colors stable, when to transition quickly, and how to preserve the mood of a scene over time.

Possible roadmap:

- Add per-LED region mapping for left, right, top, and bottom screen zones.
- Support animated LED patterns for moving objects and scene transitions.
- Extract movie palettes automatically from posters, backdrops, or video frames.
- Train GRU/RNN/LSTM models to predict better color transitions from frame history.
- Add persistent settings so Bluetooth configuration and custom palettes survive restarts.
