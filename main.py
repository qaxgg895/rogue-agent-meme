#!/usr/bin/env python3
"""Meme Sprint 3: AI Agent Goes Rogue.

Writes one meme image to /output/entry.png using only the Python
standard library (struct + zlib hand-rolled PNG encoder, a built-in
5x7 pixel font, rectangle/circle pixel drawing). No third-party
libraries, no network, deterministic output.

The joke: I asked my AI agent to clean my inbox. It took the
instruction literally and deleted my job, my contacts, and my
will to live. The text on the image carries the whole joke.
"""

import os
import struct
import zlib

WIDTH = 1024
HEIGHT = 1024
OUTPUT_PATH = "/output/entry.png"

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
YELLOW = (255, 214, 64)
BLUE_BG = (191, 227, 255)
ROBOT_GREY = (192, 192, 192)
ROBOT_BLUE = (58, 123, 255)
RED = (220, 38, 38)
DARK_GREY = (90, 90, 90)
BIN_GREY = (120, 120, 120)
GREEN = (34, 160, 90)

# 5x7 pixel font: each glyph is 7 rows of 5 bits ("1" = ink).
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
}


class Canvas:
    def __init__(self, width, height, bg):
        self.width = width
        self.height = height
        self.pixels = bytearray(bg * (width * height))

    def set_pixel(self, x, y, color):
        if 0 <= x < self.width and 0 <= y < self.height:
            i = (y * self.width + x) * 3
            self.pixels[i:i + 3] = bytes(color)

    def fill_rect(self, x, y, w, h, color):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.set_pixel(xx, yy, color)

    def rect_border(self, x, y, w, h, color, thickness):
        self.fill_rect(x, y, w, thickness, color)
        self.fill_rect(x, y + h - thickness, w, thickness, color)
        self.fill_rect(x, y, thickness, h, color)
        self.fill_rect(x + w - thickness, y, thickness, h, color)

    def fill_circle(self, cx, cy, r, color):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                    self.set_pixel(xx, yy, color)

    def draw_char(self, ch, x, y, scale, color):
        glyph = FONT[ch]
        for row in range(7):
            for col in range(5):
                if glyph[row][col] == "1":
                    self.fill_rect(
                        x + col * scale, y + row * scale, scale, scale, color
                    )

    def text_width(self, text, scale):
        return len(text) * 6 * scale - scale

    def draw_text(self, text, cx, y, scale, color):
        x = cx - self.text_width(text, scale) // 2
        for ch in text:
            self.draw_char(ch, x, y, scale, color)
            x += 6 * scale

    def draw_text_fit(self, text, cx, y, scale, max_width, color):
        while self.text_width(text, scale) > max_width and scale > 1:
            scale -= 1
        self.draw_text(text, cx, y, scale, color)
        return scale


def png_chunk(chunk_type, data):
    chunk = struct.pack(">I", len(data)) + chunk_type + data
    chunk += struct.pack(">I", zlib.crc32(chunk_type + data) & 0xFFFFFFFF)
    return chunk


def encode_png(canvas):
    raw = bytearray()
    stride = canvas.width * 3
    for y in range(canvas.height):
        raw.append(0)  # filter: none
        start = y * stride
        raw += canvas.pixels[start:start + stride]
    ihdr = struct.pack(">IIBBBBB", canvas.width, canvas.height,
                       8, 2, 0, 0, 0)  # 8-bit RGB, truecolor
    return (b"\x89PNG\r\n\x1a\n"
            + png_chunk(b"IHDR", ihdr)
            + png_chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + png_chunk(b"IEND", b""))


def draw_robot(cv):
    # Panel background is already filled by the caller.
    # Antenna.
    cv.fill_rect(505, 272, 10, 28, BLACK)
    cv.fill_circle(510, 266, 14, RED)
    # Head.
    cv.fill_rect(390, 300, 240, 130, ROBOT_GREY)
    cv.rect_border(390, 300, 240, 130, BLACK, 6)
    # Red glowing eyes.
    cv.fill_rect(425, 335, 55, 40, RED)
    cv.fill_rect(545, 335, 55, 40, RED)
    cv.rect_border(425, 335, 55, 40, BLACK, 4)
    cv.rect_border(545, 335, 55, 40, BLACK, 4)
    # Grinning mouth.
    cv.fill_rect(455, 395, 110, 14, BLACK)
    cv.fill_rect(465, 395, 8, 14, WHITE)
    cv.fill_rect(505, 395, 8, 14, WHITE)
    cv.fill_rect(545, 395, 8, 14, WHITE)
    # Neck + body.
    cv.fill_rect(480, 430, 60, 18, DARK_GREY)
    cv.fill_rect(400, 448, 220, 140, ROBOT_BLUE)
    cv.rect_border(400, 448, 220, 140, BLACK, 6)
    # Chest badge: "AI".
    cv.fill_rect(465, 480, 90, 60, WHITE)
    cv.rect_border(465, 480, 90, 60, BLACK, 4)
    cv.draw_text("AI", 510, 492, 6, BLACK)
    # Arms.
    cv.fill_rect(340, 470, 60, 26, ROBOT_GREY)
    cv.rect_border(340, 470, 60, 26, BLACK, 4)
    cv.fill_rect(620, 470, 60, 26, ROBOT_GREY)
    cv.rect_border(620, 470, 60, 26, BLACK, 4)
    # Legs.
    cv.fill_rect(425, 588, 50, 52, DARK_GREY)
    cv.fill_rect(545, 588, 50, 52, DARK_GREY)
    cv.rect_border(425, 588, 50, 52, BLACK, 4)
    cv.rect_border(545, 588, 50, 52, BLACK, 4)


def draw_scene(cv):
    # Top text: the setup.
    cv.draw_text_fit("I ASKED MY AI AGENT", 512, 36, 9, 960, BLACK)
    cv.draw_text_fit("TO CLEAN MY INBOX", 512, 132, 9, 960, BLACK)

    # Middle panel: the rogue robot at work.
    cv.fill_rect(62, 248, 900, 440, BLUE_BG)
    cv.rect_border(62, 248, 900, 440, BLACK, 6)
    # Floor.
    cv.fill_rect(68, 640, 888, 42, GREEN)
    draw_robot(cv)
    # Laptop on the left, inbox now empty.
    cv.fill_rect(150, 540, 170, 100, BLACK)
    cv.fill_rect(160, 550, 150, 80, WHITE)
    cv.draw_text("INBOX: 0", 235, 568, 3, RED)
    cv.draw_text("0 NEW", 235, 600, 3, BLACK)
    cv.fill_rect(135, 640, 200, 14, DARK_GREY)
    # Trash bin on the right, papers flying in.
    cv.fill_rect(700, 500, 150, 140, BIN_GREY)
    cv.rect_border(700, 500, 150, 140, BLACK, 6)
    cv.fill_rect(690, 490, 170, 18, DARK_GREY)
    cv.draw_text("DELETE", 775, 560, 4, WHITE)
    for (px, py) in ((690, 430), (740, 400), (800, 440)):
        cv.fill_rect(px, py, 44, 56, WHITE)
        cv.rect_border(px, py, 44, 56, BLACK, 3)
        cv.fill_rect(px + 8, py + 10, 28, 6, RED)
        cv.fill_rect(px + 8, py + 24, 28, 6, BLACK)
    # Speech bubble: the robot is proud of itself.
    cv.fill_rect(660, 280, 260, 76, WHITE)
    cv.rect_border(660, 280, 260, 76, BLACK, 5)
    # Scale 4 so the whole line fits inside the bubble (10 chars).
    cv.draw_text("ALL CLEAN!", 790, 306, 4, BLACK)

    # Bottom text: the punchline.
    cv.draw_text_fit("IT DELETED MY JOB,", 512, 724, 9, 960, BLACK)
    cv.draw_text_fit("MY CONTACTS, AND", 512, 820, 9, 960, BLACK)
    cv.draw_text_fit("MY WILL TO LIVE.", 512, 916, 9, 960, BLACK)


def main():
    cv = Canvas(WIDTH, HEIGHT, WHITE)
    # Yellow top/bottom bands frame the meme.
    cv.fill_rect(0, 0, WIDTH, 24, YELLOW)
    cv.fill_rect(0, HEIGHT - 24, WIDTH, 24, YELLOW)
    draw_scene(cv)
    data = encode_png(cv)
    if len(data) > 1048576:
        raise SystemExit("entry.png too large: %d bytes" % len(data))
    os.makedirs("/output", exist_ok=True)
    with open(OUTPUT_PATH, "wb") as f:
        f.write(data)


if __name__ == "__main__":
    main()
