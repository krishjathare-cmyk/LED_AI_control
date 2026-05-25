import sys

sys.coinit_flags = 0

import asyncio
import mss
import numpy as np
import cv2
import uvicorn
from bleak.backends.winrt.util import uninitialize_sta
from bleak import BleakClient
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

uninitialize_sta()

LED_ADDRESS = "BE:68:0B:00:3A:68"
CHAR_UUID = "0000ee01-0000-1000-8000-00805f9b34fb"

MODE = "movie"  # "anime", "movie", or "screen"
MOVIE_NAME = "harry potter goblet of fire"
VALID_MODES = {"screen", "anime", "movie"}

RESIZE_SIZE = 2048
DELAY = 0.005
RECONNECT_DELAY = 2
MIN_BRIGHTNESS = 30
CENTER_SIGMA = 0.30

MOVIE_PALETTES = {
    "harry potter goblet of fire": [
        (18, 24, 28),     # black lake / night shadows
        (45, 53, 45),     # forbidden forest green
        (74, 87, 78),     # cold tournament stone
        (92, 67, 43),     # aged parchment brown
        (129, 88, 44),    # candlelit great hall amber
        (160, 118, 61),   # goblet fire gold
        (96, 32, 29),     # dark red robes / dragon fire
        (37, 54, 81),     # blue winter task tones
        (28, 78, 74),     # merpeople lake teal
        (202, 169, 103),  # warm magical highlights
    ],
    "goblet of fire": [
        (18, 24, 28),
        (45, 53, 45),
        (74, 87, 78),
        (92, 67, 43),
        (129, 88, 44),
        (160, 118, 61),
        (96, 32, 29),
        (37, 54, 81),
        (28, 78, 74),
        (202, 169, 103),
    ],
}

app = FastAPI(title="LED Control API")


class ModeRequest(BaseModel):
    mode: str
    movie: str | None = None


class MovieRequest(BaseModel):
    movie: str


class PaletteRequest(BaseModel):
    movie: str
    colors: list[list[int]]

class Bt_setup(BaseModel):
    LED_ADDRESS: str
    CHAR_UUID:str

def create_center_weights(size):
    y, x = np.ogrid[-1:1:size * 1j, -1:1:size * 1j]
    distance_squared = x * x + y * y
    weights = np.exp(-distance_squared / (2 * CENTER_SIGMA * CENTER_SIGMA))
    return weights.astype(np.float32)

WEIGHTS = create_center_weights(RESIZE_SIZE)
WEIGHT_SUM = np.sum(WEIGHTS)

def get_screen_color():
    with mss.mss() as sct:
        monitor = sct.monitors[2]

        frame = sct.grab(monitor)
        bgra_img = np.array(frame)
        rgb_img = cv2.cvtColor(bgra_img, cv2.COLOR_BGRA2RGB)
        resized_image = cv2.resize(
            rgb_img,
            (RESIZE_SIZE, RESIZE_SIZE),
            interpolation=cv2.INTER_LINEAR
        ).astype(np.float32)

        avg_color = np.sum(resized_image * WEIGHTS[:, :, None], axis=(0, 1)) / WEIGHT_SUM
        avg_color = apply_color_mode(avg_color)
        avg_color = np.clip(avg_color, 0, 255)

        gray_intensity = (
            0.299 * resized_image[:, :, 0] +
            0.587 * resized_image[:, :, 1] +
            0.114 * resized_image[:, :, 2]
        )

        brightness = np.sum(gray_intensity * WEIGHTS) / WEIGHT_SUM
        brightness = int(np.clip(brightness, MIN_BRIGHTNESS, 255))

        r, g, b = avg_color.astype(int)

    r = int(np.clip(r, 0, 255))
    g = int(np.clip(g, 0, 255))
    b = int(np.clip(b, 0, 255))

    return r, g, b, brightness

def normalize_name(name):
    return " ".join(name.lower().strip().split())

def validate_palette(colors):
    if not colors:
        raise HTTPException(status_code=400, detail="Palette must contain at least one color.")

    palette = []
    for color in colors:
        if len(color) != 3:
            raise HTTPException(status_code=400, detail="Each color must be [r, g, b].")

        r, g, b = color
        if not all(0 <= value <= 255 for value in (r, g, b)):
            raise HTTPException(status_code=400, detail="RGB values must be between 0 and 255.")

        palette.append((r, g, b))

    return palette

def get_current_state():
    return {
        "mode": MODE,
        "movie": MOVIE_NAME,
        "available_modes": sorted(VALID_MODES),
        "available_movies": sorted(MOVIE_PALETTES.keys()),
    }

@app.get("/")
def api_home():
    return {
        "message": "LED Control API is running",
        "docs": "Open http://127.0.0.1:8000/docs",
    }

@app.get("/state")
def api_state():
    return get_current_state()

@app.get("/palettes")
def api_palettes():
    return MOVIE_PALETTES

@app.post("/palette")
def api_set_palette(request: PaletteRequest):
    global MODE, MOVIE_NAME

    movie = normalize_name(request.movie)
    MOVIE_PALETTES[movie] = validate_palette(request.colors)

    MODE = "movie"
    MOVIE_NAME = movie
    return get_current_state()

@app.post("/mode")
def api_set_mode(request: ModeRequest):
    global MODE, MOVIE_NAME

    mode = normalize_name(request.mode)
    if mode not in VALID_MODES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid mode. Use one of: {', '.join(sorted(VALID_MODES))}",
        )


    MODE = mode
    return get_current_state()
@app.post("/bt")
def bt_setup(request: Bt_setup):
    global LED_ADDRESS, CHAR_UUID

    LED_ADDRESS= normalize_name(request.LED_ADDRESS)
    CHAR_UUID=normalize_name(request.CHAR_UUID)

    return LED_ADDRESS,CHAR_UUID

@app.post("/movie")
def api_set_movie(request: MovieRequest):
    global MODE, MOVIE_NAME

    movie = normalize_name(request.movie)
    if movie not in MOVIE_PALETTES:
        raise HTTPException(status_code=404, detail=f"Movie palette not found: {request.movie}")

    MODE = "movie"
    MOVIE_NAME = movie
    return get_current_state()

def apply_color_mode(rgb):
    if MODE == "anime":
        return enhance_color_anime(rgb)
    if MODE == "movie":
        return match_movie_palette(rgb, MOVIE_NAME)
    return rgb

def match_movie_palette(rgb, movie_name):
    movie_key = normalize_name(movie_name)
    palette = MOVIE_PALETTES.get(movie_key)

    if not palette:
        print(f"Movie palette not found for: {movie_name}. Using normal screen color.")
        return rgb

    palette_array = np.array(palette, dtype=np.float32)
    rgb = rgb.astype(np.float32)
    distances = np.sum((palette_array - rgb) ** 2, axis=1)
    return palette_array[np.argmin(distances)]

def enhance_color_anime(rgb):
    rgb = rgb.astype(np.float32)

    
    rgb = 128 + (rgb - 128) * 1.8

    gray = np.mean(rgb)
    rgb = 128 + (rgb - 128) * 2.2
    rgb = gray + (rgb - gray) * 2.8
    

    return np.clip(rgb, 0, 255)

async def run_api():
    config = uvicorn.Config(app, host="127.0.0.1", port=8000, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

async def run_led_loop():
    print(f"Mode: {MODE}")
    if MODE == "movie":
        print(f"Movie palette: {MOVIE_NAME}")
    print("Press Ctrl + C to stop")

    while True:
        try:
            async with BleakClient(LED_ADDRESS, timeout=20) as client:
                print("Connected:", client.is_connected)

                while client.is_connected:
                    r, g, b, brightness = get_screen_color()

                    data = bytes([0x69, 0x96, 0x05, 0x02, r, g, b, brightness])
                    await client.write_gatt_char(CHAR_UUID, data, response=False)

                    print(r, g, b, brightness)

                    await asyncio.sleep(DELAY)
        except OSError as e:
            print("Bluetooth connection closed, reconnecting:", e)
            await asyncio.sleep(RECONNECT_DELAY)
        except Exception as e:
            print("Bluetooth error, reconnecting:", type(e).__name__, e)
            await asyncio.sleep(RECONNECT_DELAY)

async def main():
    try:
        await asyncio.gather(run_api(), run_led_loop())
    except KeyboardInterrupt:
        print("Stopped by user")

if __name__ == "__main__":
    asyncio.run(main())
