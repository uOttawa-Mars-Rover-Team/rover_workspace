#!/usr/bin/env python3
"""
Morse Code Decoder from RTSP Stream or local camera.

Timing (18 WPM, PARIS standard, dit = 66.7 ms):
  dot            = 1 unit  =  66.7 ms
  dash           = 3 units = 200.1 ms
  intra-char gap = 1 unit  =  66.7 msc:/Users/manna/Documents/Git_Repos/rover_workspace/scripts/camera_autodetect_testing/morse_code.py
  inter-letter gap = 3 units = 200.1 ms
  inter-word gap   = 7 units = 466.9 ms

Usage:
    python morse_decoder.py                          # laptop webcam
    python morse_decoder.py --camera 1               # second webcam
    python morse_decoder.py --url rtsp://IP:8554/Cam # Jetson stream
    python morse_decoder.py --show --verbose         # debug mode

    # Bloom reduction filters (use --show to compare visually):
    python morse_decoder.py --show --filter sharpen
    python morse_decoder.py --show --filter laplacian
    python morse_decoder.py --show --filter erode
    python morse_decoder.py --show --filter percentile --percentile 95

Dependencies:
    pip install opencv-python numpy
"""

import argparse
import collections
import sys
import time
from typing import Optional

import cv2
import numpy as np

# ─── Morse timing constants (milliseconds) ────────────────
DIT_MS = 66.7  # 1 unit — dot duration / base interval

DOT_MAX_MS = DIT_MS * 2.0  # <133.4 ms ON  → dot  (midpoint between 1 and 3 units)
DASH_MIN_MS = DIT_MS * 2.5  # >133.4 ms ON  → dash
INTRA_MAX_MS = DIT_MS * 2.0  # <133.4 ms OFF → same letter continues
LETTER_MIN_MS = DIT_MS * 2.5  # >133.4 ms OFF → letter boundary
LETTER_MAX_MS = (
    DIT_MS * 5.0
)  # <333.5 ms OFF → letter gap (midpoint between 3 and 7 units)
WORD_MIN_MS = DIT_MS * 6.0  # >333.5 ms OFF → word gap

SILENCE_FLUSH_MS = DIT_MS * 14.0  # flush decoder after ~2 word gaps of silence

# ─── Morse code table (ITU-R M.1677-1) ───────────────────
MORSE_TABLE = {
    # ── Letters (§1.1.1) ──────────────────────────────────
    ".-": "A",
    "-...": "B",
    "-.-.": "C",
    "-..": "D",
    ".": "E",
    "..-.": "F",
    "--.": "G",
    "....": "H",
    "..": "I",
    ".---": "J",
    "-.-": "K",
    ".-..": "L",
    "--": "M",
    "-.": "N",
    "---": "O",
    ".--.": "P",
    "--.-": "Q",
    ".-.": "R",
    "...": "S",
    "-": "T",
    "..-": "U",
    "...-": "V",
    ".--": "W",
    "-..-": "X",
    "-.--": "Y",
    "--..": "Z",
    "..-..": "É",  # accented e (ITU §1.1.1)
    # ── Figures (§1.1.2) ──────────────────────────────────
    ".----": "1",
    "..---": "2",
    "...--": "3",
    "....-": "4",
    ".....": "5",
    "-....": "6",
    "--...": "7",
    "---..": "8",
    "----.": "9",
    "-----": "0",
    # ── Punctuation & miscellaneous (§1.1.3) ──────────────
    ".-.-.-": ".",  # full stop / period
    "--..--": ",",  # comma
    "---...": ":",  # colon / division sign
    "..--..": "?",  # question mark
    ".----.": "'",  # apostrophe
    "-....-": "-",  # hyphen / dash / subtraction sign
    "-..-.": "/",  # fraction bar / division sign
    "-.--.": "(",  # left parenthesis
    "-.--.-": ")",  # right parenthesis
    ".-..-.": '"',  # inverted commas / quotation marks
    "-...-": "=",  # double hyphen (separator)
    ".-.-.": "+",  # cross / addition sign (also end-of-message AR)
    ".--.-.": "@",  # commercial at (added 2003, ITU §1.1.3)
    # ── Procedural signals / prosigns (§1.1.3) ────────────
    "...-.-": "<SK>",  # end of work
    ".-..-": "<AS>",  # wait / stand by
    "-.-.-": "<KA>",  # starting signal
    # "-.-.":    "<K>",           # invitation to transmit
    "...-.": "<UNDERSTOOD>",
    "........": "<ERROR>",  # error — 8 dots
}


def decode_symbol(symbol: str) -> str:
    return MORSE_TABLE.get(symbol, f"[?{symbol}]")


# ─── Bloom filters ────────────────────────────────────────

# Unsharp-mask kernel: boosts the bright LED core, suppresses soft halo
_SHARPEN_KERNEL = np.array(
    [
        [0, -1, 0],
        [-1, 5, -1],
        [0, -1, 0],
    ],
    dtype=np.float32,
)


def apply_filter(gray: np.ndarray, mode: str, percentile: int) -> tuple:
    """
    Apply a bloom-reduction filter to a grayscale ROI.
    Returns (filtered_gray, brightness_value).

    Modes:
      none        — raw mean (no filter)
      sharpen     — unsharp mask; crushes bloom halo, sharpens LED core
      laplacian   — aggressive edge enhancement; maximises ON/OFF contrast
      erode       — morphological erosion; shrinks bright regions, kills spread
      percentile  — uses Nth percentile instead of mean; ignores dim bloom pixels
    """
    if mode == "sharpen":
        filtered = cv2.filter2D(gray, -1, _SHARPEN_KERNEL)
        filtered = np.clip(filtered, 0, 255).astype(np.uint8)
        return filtered, float(np.mean(filtered))

    elif mode == "laplacian":
        lap = cv2.Laplacian(gray, cv2.CV_64F)
        # Add back to original so bright edges become brighter
        sharpened = np.clip(gray.astype(np.float64) + lap, 0, 255).astype(np.uint8)
        return sharpened, float(np.mean(sharpened))

    elif mode == "erode":
        # 3×3 erosion shrinks any bright blob — bloom spreads outward so
        # erosion preferentially kills the halo while leaving the hot centre
        kernel = np.ones((3, 3), np.uint8)
        eroded = cv2.erode(gray, kernel, iterations=1)
        return eroded, float(np.mean(eroded))

    elif mode == "percentile":
        # High percentile (e.g. 95) reflects the brightest pixels — the LED
        # core — rather than the dim bloom average
        brightness = float(np.percentile(gray, percentile))
        return gray, brightness

    else:  # "none"
        return gray, float(np.mean(gray))


# ─── Brightness detector ──────────────────────────────────


class BrightnessDetector:
    """
    Tracks brightness of an ROI and emits (state, duration_ms) events
    on LED ON↔OFF transitions. Uses adaptive threshold with hysteresis.
    """

    def __init__(
        self,
        threshold: Optional[float] = None,
        hysteresis: float = 10.0,
        history_len: int = 30,
    ):
        self._threshold = threshold  # None = auto-calibrate
        self._hysteresis = hysteresis
        self._history = collections.deque(maxlen=history_len)
        self._state = None  # True=ON, False=OFF
        self._state_start_ms = None

    def _auto_threshold(self) -> float:
        if len(self._history) < 2:
            return 128.0
        return (min(self._history) + max(self._history)) / 2.0

    def push(self, brightness: float, ts_ms: float):
        """
        Feed a brightness sample at timestamp ts_ms (milliseconds).
        Returns (state, duration_ms) on transition, else None.
        """
        self._history.append(brightness)
        thresh = self._threshold or self._auto_threshold()
        hi = thresh + self._hysteresis / 2
        lo = thresh - self._hysteresis / 2

        new_state = None
        if brightness > hi:
            new_state = True  # LED ON
        elif brightness < lo:
            new_state = False  # LED OFF

        if new_state is None or new_state == self._state:
            return None

        event = None
        if self._state is not None and self._state_start_ms is not None:
            duration_ms = ts_ms - self._state_start_ms
            event = (self._state, duration_ms)

        self._state = new_state
        self._state_start_ms = ts_ms
        return event


# ─── Morse decoder state machine ──────────────────────────


class MorseDecoder:
    def __init__(self, verbose: bool = False):
        self._verbose = verbose
        self._symbol = ""
        self._word = ""

    def _flush_symbol(self):
        if not self._symbol:
            return
        ch = decode_symbol(self._symbol)
        if self._verbose:
            print(f"  letter: {self._symbol!r:12s} → {ch}")
        self._word += ch
        self._symbol = ""

    def _flush_word(self):
        self._flush_symbol()
        if self._word:
            print(f"\n>>> WORD: {self._word}\n", flush=True)
        self._word = ""

    def feed(self, state: bool, duration_ms: float):
        if state:
            if duration_ms <= DOT_MAX_MS:
                self._symbol += "."
                if self._verbose:
                    print(f"  dot  ({duration_ms:.0f} ms)")
            else:
                self._symbol += "-"
                if self._verbose:
                    print(f"  dash ({duration_ms:.0f} ms)")
        else:
            if duration_ms <= INTRA_MAX_MS:
                if self._verbose:
                    print(f"  [intra-char gap  {duration_ms:.0f} ms]")
            elif duration_ms <= LETTER_MAX_MS:
                if self._verbose:
                    print(f"  [letter gap  {duration_ms:.0f} ms]")
                self._flush_symbol()
            else:
                if self._verbose:
                    print(f"  [word gap  {duration_ms:.0f} ms]")
                self._flush_word()

    def flush(self):
        self._flush_word()


# ─── Main loop ────────────────────────────────────────────


def run(
    source,
    roi: Optional[tuple],
    show: bool,
    threshold: Optional[float],
    verbose: bool,
    filter_mode: str,
    percentile: int,
    exposure: Optional[int],
) -> None:

    if isinstance(source, int):
        cap = cv2.VideoCapture(source)
        source_label = f"laptop camera (index {source})"
    else:
        cap = cv2.VideoCapture(source, cv2.CAP_FFMPEG)
        source_label = source

    if not cap.isOpened():
        print(f"ERROR: cannot open {source_label}", file=sys.stderr)
        sys.exit(1)

    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    # Force manual exposure so the LED doesn't bloom across the whole frame.
    # Auto-exposure cranks gain up for the dark background, saturating the LED.
    if exposure is not None:
        # CAP_PROP_AUTO_EXPOSURE: 0.25 = manual, 0.75 = auto (OpenCV convention)
        cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)
        cap.set(cv2.CAP_PROP_EXPOSURE, exposure)
        actual = cap.get(cv2.CAP_PROP_EXPOSURE)
        print(f"Exposure:     {exposure} (camera reported {actual})")
    else:
        print("Exposure:     auto  (use --exposure -6 to darken, try -4 to -8)")

    detector = BrightnessDetector(threshold=threshold)
    decoder = MorseDecoder(verbose=verbose)

    print(f"Connected to  {source_label}")
    print(
        f"Filter:       {filter_mode}"
        + (f"  (p{percentile})" if filter_mode == "percentile" else "")
    )
    if roi:
        print(f"ROI:          x={roi[0]} y={roi[1]} w={roi[2]} h={roi[3]}")
    else:
        print("ROI:          full frame (use --roi x y w h to narrow focus)")
    print(
        f"Timing:       dit={DIT_MS:.1f} ms  "
        f"dot<{DOT_MAX_MS:.1f}  letter<{LETTER_MAX_MS:.1f}  word>{WORD_MIN_MS:.1f}"
    )
    print("Decoding Morse … (Ctrl-C to stop)\n")

    last_event_ms = time.monotonic() * 1000

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Stream ended or lost.", file=sys.stderr)
                break

            ts_ms = time.monotonic() * 1000

            region = (
                frame[roi[1] : roi[1] + roi[3], roi[0] : roi[0] + roi[2]]
                if roi
                else frame
            )

            gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
            filtered_gray, brightness = apply_filter(gray, filter_mode, percentile)

            event = detector.push(brightness, ts_ms)
            if event is not None:
                state, duration_ms = event
                decoder.feed(state, duration_ms)
                last_event_ms = ts_ms

            if ts_ms - last_event_ms > SILENCE_FLUSH_MS:
                decoder.flush()
                last_event_ms = ts_ms

            if show:
                # Show the filtered grayscale in the ROI so you can see
                # what the detector actually "sees" after filtering
                display = frame.copy()
                if roi:
                    x, y, w, h = roi
                    # Replace ROI in display with filtered (converted back to BGR)
                    display[y : y + h, x : x + w] = cv2.cvtColor(
                        filtered_gray, cv2.COLOR_GRAY2BGR
                    )
                    cv2.rectangle(display, (x, y), (x + w, y + h), (0, 255, 0), 2)

                bar_w = int(min(brightness, 255) / 255 * display.shape[1])
                cv2.rectangle(display, (0, 0), (bar_w, 8), (0, 255, 0), -1)
                cv2.putText(
                    display,
                    f"brightness: {brightness:.0f}  filter: {filter_mode}",
                    (10, 24),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 0),
                    1,
                )
                cv2.imshow("Morse Decoder", display)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

    except KeyboardInterrupt:
        print("\nInterrupted.")
    finally:
        decoder.flush()
        cap.release()
        if show:
            cv2.destroyAllWindows()


# ─── CLI ──────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Decode Morse code from an LED visible to a camera.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python morse_decoder.py                               # laptop webcam\n"
            "  python morse_decoder.py --camera 1                    # second webcam\n"
            "  python morse_decoder.py --url rtsp://IP:8554/FrontCam\n"
            "  python morse_decoder.py --show --verbose              # debug mode\n"
            "\n"
            "  # Bloom reduction (compare visually with --show):\n"
            "  python morse_decoder.py --show --filter sharpen\n"
            "  python morse_decoder.py --show --filter laplacian\n"
            "  python morse_decoder.py --show --filter erode\n"
            "  python morse_decoder.py --show --filter percentile --percentile 95\n"
        ),
    )
    src = parser.add_mutually_exclusive_group()
    src.add_argument(
        "--camera",
        "-c",
        type=int,
        default=None,
        metavar="N",
        help="Laptop/USB camera index (default: 0)",
    )
    src.add_argument(
        "--url", "-u", type=str, default=None, metavar="URL", help="RTSP or file URL"
    )

    parser.add_argument(
        "--roi",
        nargs=4,
        type=int,
        metavar=("X", "Y", "W", "H"),
        help="Region of interest in pixels (x y width height)",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Display video window; ROI shows the filtered image the detector sees",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=None,
        help="Fixed brightness threshold 0-255 (default: auto-calibrate)",
    )
    parser.add_argument(
        "--exposure",
        type=int,
        default=None,
        metavar="N",
        help=(
            "Camera exposure value (negative log2 seconds, e.g. -6 = 1/64 s). "
            "Locks manual exposure to prevent auto-gain blooming the LED. "
            "Try -4 (bright) to -8 (dark). Default: auto."
        ),
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print every dot/dash/gap event with timing",
    )
    parser.add_argument(
        "--filter",
        dest="filter_mode",
        choices=["none", "sharpen", "laplacian", "erode", "percentile"],
        default="none",
        help=(
            "Bloom reduction filter (default: none):\n"
            "  none        raw mean brightness\n"
            "  sharpen     unsharp mask — crushes halo, sharpens LED core\n"
            "  laplacian   aggressive edge boost — maximises ON/OFF contrast\n"
            "  erode       morphological erosion — shrinks bright blobs\n"
            "  percentile  use Nth percentile instead of mean (see --percentile)\n"
        ),
    )
    parser.add_argument(
        "--percentile",
        type=int,
        default=95,
        metavar="N",
        help="Percentile to use with --filter percentile (default: 95)",
    )

    args = parser.parse_args()

    source = args.url if args.url else (args.camera if args.camera is not None else 0)
    roi = tuple(args.roi) if args.roi else None
    run(
        source,
        roi,
        args.show,
        args.threshold,
        args.verbose,
        args.filter_mode,
        args.percentile,
        args.exposure,
    )


if __name__ == "__main__":
    main()
