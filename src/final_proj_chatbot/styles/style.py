"""Visual theme for the Power Scaling app: TOML-driven arena lobby, gravel grain, heartbeat spotlight.

Reads colors and radius directly from `.streamlit/config.toml` (`[theme]`), and optionally
loads extra arena/gravel/pulse settings from `.streamlit/arena_theme.toml`.

Call `inject_styles()` (or `inject_styles(scale="planetary")`) once right after `st.set_page_config(...)`.
"""

from pathlib import Path
from typing import Any, Union
import streamlit as st

try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11 fallback
    tomllib = None  # type: ignore[assignment]


# ---------- color & TOML helpers ----------

def _parse_hex(color: str) -> tuple[int, int, int]:
    """Convert #RGB, #RRGGBB, or #RRGGBBAA into an (r, g, b) tuple."""
    h = color.strip().lstrip("#")
    if len(h) == 3:
        h = "".join(ch * 2 for ch in h)
    elif len(h) == 8:
        h = h[:6]
    if len(h) != 6:
        return (29, 23, 21)
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _to_hex(rgb: tuple[int, int, int]) -> str:
    r, g, b = (max(0, min(255, round(c))) for c in rgb)
    return f"#{r:02X}{g:02X}{b:02X}"


def _mix(c1: str, c2: str, weight: float) -> str:
    """Blend c1 toward c2 by weight (0.0 = c1, 1.0 = c2)."""
    r1, g1, b1 = _parse_hex(c1)
    r2, g2, b2 = _parse_hex(c2)
    w = max(0.0, min(1.0, weight))
    return _to_hex((
        r1 + (r2 - r1) * w,
        g1 + (g2 - g1) * w,
        b1 + (b2 - b1) * w,
    ))


def _rgba(color: str, alpha: float) -> str:
    r, g, b = _parse_hex(color)
    return f"rgba({r}, {g}, {b}, {alpha:.3f})"


def _contrast_ink(bg_hex: str) -> str:
    """Pick dark or light text for high readability on top of `bg_hex` (e.g. gold buttons)."""
    r, g, b = (c / 255.0 for c in _parse_hex(bg_hex))
    luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
    return "#14110F" if luminance > 0.52 else "#FFFFFF"


def _normalize_radius(raw: Any) -> str:
    if not raw:
        return "4px"
    val = str(raw).strip().lower()
    presets = {
        "none": "0px",
        "small": "2px",
        "medium": "4px",
        "large": "8px",
        "full": "9999px",
    }
    return presets.get(val, str(raw).strip())


def _load_arena_toml() -> dict[str, Any]:
    """Load optional `.streamlit/arena_theme.toml` or `arena_theme.toml` if present."""
    if tomllib is None:
        return {}
    for candidate in (Path(".streamlit/arena_theme.toml"), Path("arena_theme.toml")):
        if candidate.is_file():
            try:
                return tomllib.loads(candidate.read_text(encoding="utf-8"))
            except Exception:
                return {}
    return {}


def _build_gravel_svg(frequency: float) -> str:
    """Build inline SVG gravel noise data URI. '<' and '>' stay percent-encoded."""
    freq = max(0.2, min(1.5, float(frequency)))
    return (
        'url("data:image/svg+xml;utf8,'
        "%3Csvg xmlns='http://www.w3.org/2000/svg' width='220' height='220'%3E"
        "%3Cfilter id='gravel'%3E"
        f"%3CfeTurbulence type='fractalNoise' baseFrequency='{freq:.2f}' numOctaves='4' seed='7' stitchTiles='stitch'/%3E"
        "%3CfeColorMatrix type='saturate' values='0'/%3E"
        "%3CfeComponentTransfer%3E"
        "%3CfeFuncR type='linear' slope='1.55' intercept='-0.27'/%3E"
        "%3CfeFuncG type='linear' slope='1.55' intercept='-0.27'/%3E"
        "%3CfeFuncB type='linear' slope='1.55' intercept='-0.27'/%3E"
        "%3C/feComponentTransfer%3E"
        "%3C/filter%3E"
        "%3Crect width='100%25' height='100%25' filter='url(%23gravel)'/%3E"
        '%3C/svg%3E")'
    )


_DEFAULT_SCALE_HEX: dict[str, str] = {
    "street": "#8A9BB8",
    "city": "#40A6CC",
    "planetary": "#7A74E8",
    "stellar": "#E08444",
    "cosmic": "#A85CE4",
}

_SCALE_ALIASES: dict[str, str] = {
    "wall": "street",
    "building": "street",
    "town": "city",
    "mountain": "city",
    "island": "city",
    "country": "planetary",
    "continental": "planetary",
    "moon": "planetary",
    "planet": "planetary",
    "star": "stellar",
    "solar": "stellar",
    "galaxy": "cosmic",
    "universal": "cosmic",
    "multiversal": "cosmic",
    "outer": "cosmic",
}


def _resolve_spotlight_hex(
    scale: Union[str, int, float, None],
    primary_hex: str,
    custom_scales: dict[str, str],
) -> str:
    """Use `primaryColor` by default, or shift to a tier color when `scale` is provided."""
    if scale is None:
        return primary_hex

    palette = {**_DEFAULT_SCALE_HEX, **{k.lower(): v for k, v in custom_scales.items()}}

    if isinstance(scale, (int, float)):
        if scale <= 2:
            return palette["street"]
        if scale <= 4:
            return palette["city"]
        if scale <= 6:
            return palette["planetary"]
        if scale <= 8:
            return palette["stellar"]
        return palette["cosmic"]

    key = scale.strip().lower()
    resolved = _SCALE_ALIASES.get(key, key)
    return palette.get(resolved, primary_hex)


_FONTS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700');
"""

_CSS = """
:root {
  --bg: __BG__;
  --bg-top: __BG_TOP__;
  --bg-mid: __BG_MID__;
  --bg-deep: __BG_DEEP__;
  --vignette: __VIGNETTE__;
  --surface: __SURFACE__;
  --surface-solid: __SURFACE_SOLID__;
  --raised: __RAISED__;
  --raised-hover: __RAISED_HOVER__;
  --field: __FIELD__;
  --edge: __EDGE__;
  --edge-strong: __EDGE_STRONG__;
  --edge-lit: __EDGE_LIT__;
  --spot-core: __SPOT_CORE__;
  --spot-mid: __SPOT_MID__;
  --spot-fade: __SPOT_FADE__;
  --spot-rim: __SPOT_RIM__;
  --spot-hue-shift: __HUE_SHIFT__;
  --ink: __INK__;
  --ink-soft: __INK_SOFT__;
  --ink-faint: __INK_FAINT__;
  --accent: __ACCENT__;
  --accent-top: __ACCENT_TOP__;
  --accent-hover: __ACCENT_HOVER__;
  --accent-ink: __ACCENT_INK__;
  --accent-fg: __ACCENT_FG__;
  --accent-glow: __ACCENT_GLOW__;
  --accent-tint: __ACCENT_TINT__;
  --danger: #E58A8A;
  --radius: __RADIUS__;
  --gravel: __GRAVEL__;
  --gravel-opacity: __GRAVEL_OPACITY__;
  --card-blur: __CARD_BLUR__;
  --max-width: __MAX_WIDTH__;
  --pulse-duration: __PULSE_DURATION__;
}

/* ---------- heartbeat spotlight animation ---------- */
@keyframes arena-heartbeat {
  0% {
    transform: scale(0.88);
    opacity: 0.64;
    filter: hue-rotate(0deg);
    animation-timing-function: cubic-bezier(0.16, 1, 0.3, 1);
  }
  __PULSE_PEAK_PCT__ {
    transform: scale(1.22);
    opacity: 1;
    filter: hue-rotate(var(--spot-hue-shift));
    animation-timing-function: cubic-bezier(0.32, 0.04, 0.25, 1);
  }
  100% {
    transform: scale(0.88);
    opacity: 0.64;
    filter: hue-rotate(0deg);
  }
}

/* ---------- arena lobby stage & lighting ---------- */
html, body {
  background-color: var(--bg);
  color: var(--ink);
}

html, body, .stApp, [data-testid="stAppViewContainer"], p, label, input, textarea, button {
  font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', sans-serif;
}

.stApp {
  background: linear-gradient(180deg, var(--bg-top) 0%, var(--bg-mid) 60%, var(--bg-deep) 100%);
  color: var(--ink);
}

/* Full-bleed spotlight canvas (oversized to avoid edge clipping at peak scale) */
.stApp::before {
  content: "";
  position: fixed;
  inset: -35%;
  transform: scale(0.88);
  transform-origin: 50% 22%;
  background:
    radial-gradient(ellipse 36% 28% at 50% 22%, var(--spot-core) 0%, var(--spot-mid) 40%, var(--spot-fade) 74%),
    radial-gradient(ellipse 24% 20% at 32% 28%, var(--spot-rim) 0%, var(--spot-fade) 68%);
  animation: arena-heartbeat var(--pulse-duration) infinite;
  will-change: transform, opacity, filter;
  pointer-events: none;
  z-index: 0;
}

/* Gravel aggregate texture reacting to the pulsing light */
.stApp::after {
  content: "";
  position: fixed;
  inset: 0;
  background-image: var(--gravel);
  background-size: 220px 220px;
  opacity: var(--gravel-opacity);
  mix-blend-mode: overlay;
  pointer-events: none;
  z-index: 0;
}

/* Transparent inner container + perimeter vignette */
[data-testid="stAppViewContainer"] {
  background: transparent !important;
}
[data-testid="stAppViewContainer"]::before {
  content: "";
  position: fixed;
  inset: 0;
  background: radial-gradient(circle at 50% 30%, transparent 44%, var(--vignette) 100%);
  pointer-events: none;
  z-index: 0;
}

/* Keep UI layers crisp above the background lighting */
[data-testid="stMain"], [data-testid="stHeader"], [data-testid="stSidebar"] {
  position: relative;
  z-index: 1;
}

[data-testid="stHeader"] { background: transparent; }
[data-testid="stMainBlockContainer"] { max-width: var(--max-width); padding-top: 5rem; }

@media (prefers-reduced-motion: reduce) {
  .stApp::before {
    animation: none;
    transform: scale(1);
    opacity: 0.85;
  }
}

/* ---------- cards ---------- */
.st-key-profile_card, .st-key-feats_card {
  background: var(--surface);
  backdrop-filter: blur(var(--card-blur));
  -webkit-backdrop-filter: blur(var(--card-blur));
  border: 1px solid var(--edge);
  border-top-color: var(--edge-lit);
  border-radius: var(--radius);
  padding: 1.25rem;
  box-shadow:
    0 14px 34px rgba(0, 0, 0, 0.48),
    inset 0 1px 0 rgba(255, 255, 255, 0.05);
}

/* ---------- portrait ---------- */
.pw-portrait {
  display: block;
  width: 100%;
  aspect-ratio: 3 / 4;
  object-fit: cover;
  border: 1px solid var(--edge-strong);
  border-top-color: var(--edge-lit);
  border-radius: var(--radius);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.42);
}
.pw-portrait--empty {
  display: flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
  background: linear-gradient(180deg, var(--raised) 0%, var(--field) 100%);
  border-style: dashed;
  color: var(--ink-soft);
  font-size: .9rem;
  font-weight: 500;
}

/* ---------- labels, inputs ---------- */
[data-testid="stWidgetLabel"] p, .pw-label {
  font-size: .8rem;
  font-weight: 600;
  color: var(--ink-soft);
}
.pw-label { margin: .5rem 0 .3rem; }

div[data-baseweb="input"] {
  background: var(--field) !important;
  border: 1px solid var(--edge) !important;
  border-radius: var(--radius) !important;
  box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.45);
}
div[data-baseweb="base-input"] { background: transparent !important; }
div[data-baseweb="input"]:focus-within {
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 1px var(--accent), 0 0 14px var(--accent-glow) !important;
}
.stApp input { color: var(--ink) !important; font-weight: 500; }
.stApp input::placeholder { color: var(--ink-faint) !important; font-weight: 400; }

[data-testid="stFileUploaderDropzone"] {
  background: var(--field);
  border-color: var(--edge);
  border-radius: var(--radius);
}
[data-testid="stToast"] { border-radius: var(--radius); }

/* ---------- buttons ---------- */
button:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }

[data-testid^="stBaseButton-secondary"] {
  background: var(--raised);
  border: 1px solid var(--edge-strong);
  border-top-color: rgba(255, 255, 255, 0.12);
  border-radius: var(--radius);
  color: var(--ink);
  font-weight: 500;
  transition: background-color 140ms ease, border-color 140ms ease, box-shadow 140ms ease;
}
[data-testid^="stBaseButton-secondary"]:hover {
  background: var(--raised-hover);
  border-color: var(--ink-faint);
  color: var(--ink);
}
[data-testid="stBaseButton-primary"] {
  background: linear-gradient(180deg, var(--accent-top) 0%, var(--accent) 100%);
  border: 1px solid var(--accent);
  border-top-color: var(--accent-hover);
  border-radius: var(--radius);
  color: var(--accent-fg);
  font-weight: 600;
  padding: .55rem 1rem;
  box-shadow: 0 2px 12px var(--accent-glow);
  transition: background 140ms ease, box-shadow 140ms ease;
}
[data-testid="stBaseButton-primary"]:hover {
  background: var(--accent-hover);
  border-color: var(--accent-hover);
  box-shadow: 0 4px 18px var(--accent-glow);
  color: var(--accent-fg);
}

[data-testid="stPopoverBody"] {
  background: var(--surface-solid);
  border: 1px solid var(--edge-strong);
  border-radius: var(--radius);
  box-shadow: 0 12px 28px rgba(0, 0, 0, 0.55);
}

/* ---------- power-up chips ---------- */
.st-key-powerups_row {
  gap: .4rem;
  padding: .6rem;
  min-height: 3.2rem;
  background: var(--field);
  border: 1px solid var(--edge);
  border-radius: var(--radius);
  box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.45);
}
.st-key-powerups_row button {
  min-height: 0;
  padding: .15rem .65rem;
}
.st-key-powerups_row button p { font-size: .8rem; font-weight: 500; }
.st-key-powerups_row button:hover { border-color: var(--accent); }
.st-key-powerups_row [data-testid="stPopover"] button {   /* the "Add" chip */
  background: transparent;
  border-style: dashed;
  color: var(--accent-ink);
}

/* ---------- feats ---------- */
.pw-title {
  font-size: 1.15rem;
  font-weight: 600;
  letter-spacing: 0.01em;
  color: var(--ink);
  margin: 0 0 1rem;
  padding-bottom: .75rem;
  border-bottom: 1px solid var(--edge);
}
.st-key-feats_scroll {
  background: var(--field);
  border: 1px solid var(--edge);
  border-radius: var(--radius);
  padding: .6rem;
  box-shadow: inset 0 1px 4px rgba(0, 0, 0, 0.5);
}
.pw-empty {
  text-align: center;
  color: var(--ink-faint);
  font-size: .9rem;
  padding: 4rem 1rem;
}
[class*="st-key-feat_card_"] {
  background: linear-gradient(90deg, var(--accent-tint) 0%, var(--raised) 32%);
  border: 1px solid var(--edge);
  border-left: 3px solid var(--accent);
  border-radius: var(--radius);
  padding: .75rem 1rem;
  transition: border-color 140ms ease, background 140ms ease;
}
[class*="st-key-feat_card_"]:hover {
  border-color: var(--edge-strong);
  border-left-color: var(--accent-hover);
}
[class*="st-key-feat_card_"] p {
  margin: 0;
  font-size: .95rem;
  line-height: 1.5;
  color: var(--ink);
}
[class*="st-key-feat_x_"] button {
  width: 1.75rem;
  height: 1.75rem;
  min-height: 0;
  padding: 0;
  background: transparent;
  border: none;
  color: var(--ink-soft);
}
[class*="st-key-feat_x_"] button:hover {
  background: rgba(229, 138, 138, .14);
  color: var(--danger);
}

/* ---------- feat search bar ---------- */
.st-key-feat_bar { margin-top: .9rem; }
.st-key-feat_bar [data-testid="stFormSubmitButton"] button {
  width: 2.5rem;
  height: 2.5rem;
  padding: 0;
  background: linear-gradient(180deg, var(--accent-top) 0%, var(--accent) 100%);
  border: 1px solid var(--accent);
  border-top-color: var(--accent-hover);
  color: var(--accent-fg);
}
.st-key-feat_bar [data-testid="stFormSubmitButton"] button:hover {
  background: var(--accent-hover);
  border-color: var(--accent-hover);
  color: var(--accent-fg);
}

/* ---------- arena stage & fighter cards ---------- */
.pw-fighter-frame {
  background: var(--surface);
  backdrop-filter: blur(var(--card-blur));
  -webkit-backdrop-filter: blur(var(--card-blur));
  border: 1px solid var(--edge-strong);
  border-top-color: var(--edge-lit);
  border-radius: var(--radius);
  padding: 0.55rem;
  box-shadow:
    0 16px 36px rgba(0, 0, 0, 0.52),
    inset 0 1px 0 rgba(255, 255, 255, 0.06);
  transition: border-color 180ms ease, box-shadow 180ms ease;
}
.pw-fighter-frame--active {
  border-color: var(--edge-lit);
  box-shadow:
    0 18px 42px rgba(0, 0, 0, 0.58),
    0 0 24px var(--accent-glow);
}

.pw-fighter-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  margin-top: 0.5rem;
  padding: 0.35rem 0.5rem;
  background: var(--field);
  border: 1px solid var(--edge);
  border-radius: var(--radius);
  font-size: 0.76rem;
  color: var(--ink-soft);
}
.pw-fighter-tag {
  font-weight: 600;
  color: var(--accent-ink);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  font-size: 0.7rem;
}

/* Locked fighter nameplate shown underneath portraits during a fight */
.pw-fighter-plate {
  margin-top: 0.65rem;
  padding: 0.55rem 0.85rem;
  background: var(--surface);
  border: 1px solid var(--edge-strong);
  border-left: 3px solid var(--accent);
  border-radius: var(--radius);
  color: var(--ink);
  font-size: 0.98rem;
  font-weight: 600;
  letter-spacing: 0.01em;
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.35);
}

/* Center VS emblem (large pre-fight, compact crown badge in-fight) */
.pw-vs-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  user-select: none;
}
.pw-vs-wrap--lobby {
  min-height: 290px;
}
.pw-vs-wrap--crown {
  position: relative;
  z-index: 3;
  margin-bottom: -24px;
  pointer-events: none;
}

/* Prominent FIGHT trigger button */
.st-key-fight_btn_wrap {
  margin-top: 0.5rem;
}
.st-key-fight_btn_wrap [data-testid="stBaseButton-primary"] {
  font-size: 1.05rem;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  padding: 0.8rem 1.5rem;
  box-shadow:
    0 6px 22px var(--accent-glow),
    0 4px 0 rgba(0, 0, 0, 0.45);
}
.st-key-fight_btn_wrap [data-testid="stBaseButton-primary"]:hover {
  transform: translateY(-1px);
  box-shadow:
    0 8px 28px var(--accent-glow),
    0 5px 0 rgba(0, 0, 0, 0.5);
}

/* ---------- center narration arena box ---------- */
.pw-narration-box {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  min-height: 410px;
  padding: 2.75rem 2rem 2rem;
  background: linear-gradient(180deg, rgba(20, 23, 29, 0.88) 0%, var(--surface) 100%);
  backdrop-filter: blur(var(--card-blur));
  -webkit-backdrop-filter: blur(var(--card-blur));
  border: 1px solid var(--edge-strong);
  border-top-color: var(--edge-lit);
  border-radius: var(--radius);
  box-shadow:
    0 18px 44px rgba(0, 0, 0, 0.56),
    inset 0 1px 0 rgba(255, 255, 255, 0.06),
    inset 0 0 48px rgba(0, 0, 0, 0.35);
  overflow: hidden;
}

@keyframes pw-narration-new {
  0% {
    opacity: 0;
    transform: translateY(18px) scale(0.94);
  }
  100% {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

@keyframes pw-narration-old {
  0% {
    opacity: 0.95;
    transform: translateY(24px) scale(1.12);
  }
  100% {
    opacity: 0.42;
    transform: translateY(0) scale(1);
  }
}

.pw-narration-history {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.45rem;
  margin-bottom: 1.1rem;
  max-width: 90%;
}

.pw-narration-prev {
  font-size: 0.98rem;
  font-weight: 500;
  color: var(--ink-soft);
  opacity: 0.42;
  line-height: 1.4;
  animation: pw-narration-old 380ms cubic-bezier(0.22, 1, 0.36, 1) both;
}

.pw-narration-prev--faded {
  font-size: 0.82rem;
  opacity: 0.20;
}

.pw-narration-current {
  font-size: 1.55rem;
  font-weight: 700;
  line-height: 1.35;
  color: var(--ink);
  max-width: 92%;
  text-shadow: 0 2px 18px rgba(0, 0, 0, 0.65);
  animation: pw-narration-new 420ms cubic-bezier(0.16, 1, 0.3, 1) both;
}

.pw-narration-placeholder {
  font-size: 1rem;
  font-weight: 500;
  color: var(--ink-faint);
  letter-spacing: 0.02em;
}

"""


def inject_styles(
    scale: Union[str, int, float, None] = None,
    **overrides: Any,
) -> None:
    """Apply the Power Scaling theme to the current page.

    Colors and base radius are read live from `.streamlit/config.toml` (`[theme]`).
    Extra visual settings can be configured in `.streamlit/arena_theme.toml` (`[arena]`)
    or passed as keyword overrides to `inject_styles(...)`.
    """
    # 1. Read active Streamlit [theme] options from config.toml
    primary = st.get_option("theme.primaryColor") or "#e0aa2d"
    bg = st.get_option("theme.backgroundColor") or "#1d1715"
    surface_hex = st.get_option("theme.secondaryBackgroundColor") or "#271d1c"
    text = st.get_option("theme.textColor") or "#E4E8EE"
    radius = _normalize_radius(st.get_option("theme.baseRadius"))

    # 2. Load optional arena_theme.toml + apply any direct keyword overrides
    cfg_file = _load_arena_toml()
    arena_cfg = {**cfg_file.get("arena", {}), **overrides}
    custom_scales = cfg_file.get("scales", {})

    gravel_opacity = float(arena_cfg.get("gravel_opacity", 0.22))
    gravel_freq = float(arena_cfg.get("gravel_frequency", 0.58))
    pulse_out_s = float(arena_cfg.get("pulse_out_s", 1.0))
    pulse_in_s = float(arena_cfg.get("pulse_in_s", 3.0))
    spot_intensity = float(arena_cfg.get("spotlight_intensity", 0.28))
    hue_shift_deg = float(arena_cfg.get("hue_shift_deg", 14))
    card_opacity = float(arena_cfg.get("card_opacity", 0.84))
    card_blur_px = int(arena_cfg.get("card_blur_px", 10))
    max_width_px = int(arena_cfg.get("max_width_px", 1100))

    total_pulse_s = max(0.2, pulse_out_s + pulse_in_s)
    peak_pct = f"{(pulse_out_s / total_pulse_s) * 100:.2f}%"

    # 3. Derive full UI & arena lighting palette from config.toml colors
    spot_hex = _resolve_spotlight_hex(scale, primary, custom_scales)
    rim_hex = _mix(spot_hex, text, 0.42)

    tokens = {
        "__BG__": bg,
        "__BG_TOP__": _rgba(_mix(bg, surface_hex, 0.55), 0.42),
        "__BG_MID__": _rgba(bg, 0.82),
        "__BG_DEEP__": _mix(bg, "#000000", 0.46),
        "__VIGNETTE__": _rgba(_mix(bg, "#000000", 0.65), 0.72),
        "__SURFACE__": _rgba(surface_hex, card_opacity),
        "__SURFACE_SOLID__": surface_hex,
        "__RAISED__": _mix(surface_hex, text, 0.06),
        "__RAISED_HOVER__": _mix(surface_hex, text, 0.11),
        "__FIELD__": _mix(bg, "#000000", 0.24),
        "__EDGE__": _mix(surface_hex, text, 0.14),
        "__EDGE_STRONG__": _mix(surface_hex, text, 0.24),
        "__EDGE_LIT__": _rgba(rim_hex, 0.26),
        "__SPOT_CORE__": _rgba(spot_hex, spot_intensity),
        "__SPOT_MID__": _rgba(spot_hex, spot_intensity * 0.40),
        "__SPOT_FADE__": _rgba(spot_hex, 0.0),
        "__SPOT_RIM__": _rgba(rim_hex, spot_intensity * 0.30),
        "__HUE_SHIFT__": f"{hue_shift_deg:g}deg",
        "__INK__": text,
        "__INK_SOFT__": _mix(text, bg, 0.35),
        "__INK_FAINT__": _mix(text, bg, 0.55),
        "__ACCENT__": primary,
        "__ACCENT_TOP__": _mix(primary, "#FFFFFF", 0.10),
        "__ACCENT_HOVER__": _mix(primary, "#FFFFFF", 0.18),
        "__ACCENT_INK__": _mix(primary, text, 0.42),
        "__ACCENT_FG__": _contrast_ink(primary),
        "__ACCENT_GLOW__": _rgba(primary, 0.28),
        "__ACCENT_TINT__": _rgba(primary, 0.12),
        "__RADIUS__": radius,
        "__GRAVEL__": _build_gravel_svg(gravel_freq),
        "__GRAVEL_OPACITY__": f"{gravel_opacity:.3f}",
        "__CARD_BLUR__": f"{card_blur_px}px",
        "__MAX_WIDTH__": f"{max_width_px}px",
        "__PULSE_DURATION__": f"{total_pulse_s:g}s",
        "__PULSE_PEAK_PCT__": peak_pct,
    }

    css = _FONTS + _CSS
    for key, value in tokens.items():
        css = css.replace(key, value)

    st.html(f"<style>{css}</style>")