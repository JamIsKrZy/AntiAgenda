"""Visual theme for the Power Scaling app: dark, restrained, 4px corners.

Call `inject_styles()` once, right after `st.set_page_config(...)`.
Everything visual lives here so page files only deal with layout and logic.

Palette
    background  #15181D   page
    surface     #1C2027   cards
    raised      #242932   chips, feat cards, buttons
    field       #12151A   inputs and list wells
    edge        #313845   borders
    text        #E4E8EE   primary text (soft: #9099A9)
    accent      #4A78D0   primary actions, focus, feat marker
"""

import streamlit as st

# Very fine film grain as an inline SVG. "<" and ">" are percent-encoded so the
# HTML sanitizer doesn't mistake the data URI for markup.
_GRAIN = (
    'url("data:image/svg+xml;utf8,'
    "%3Csvg xmlns='http://www.w3.org/2000/svg' width='240' height='240'%3E"
    "%3Cfilter id='g'%3E"
    "%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='3' stitchTiles='stitch'/%3E"
    "%3CfeColorMatrix type='saturate' values='0'/%3E"
    "%3C/filter%3E"
    "%3Crect width='100%25' height='100%25' filter='url(%23g)'/%3E"
    '%3C/svg%3E")'
)

_FONTS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700');
"""

_CSS = """
:root {
  --bg: #15181D;
  --surface: #1C2027;
  --raised: #242932;
  --raised-hover: #2B313C;
  --field: #12151A;
  --edge: #313845;
  --edge-strong: #434C5C;
  --ink: #E4E8EE;
  --ink-soft: #9099A9;
  --ink-faint: #6B7485;
  --accent: #4A78D0;
  --accent-hover: #5A87DE;
  --accent-ink: #9DBBF2;
  --danger: #E58A8A;
  --radius: 4px;
  --grain: __GRAIN__;
}

/* ---------- page ---------- */
html, body, .stApp, [data-testid="stAppViewContainer"], p, label, input, textarea, button {
  font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', sans-serif;
}
.stApp { background-color: var(--bg); color: var(--ink); }
.stApp::before {               /* barely-there grain over everything */
  content: "";
  position: fixed;
  inset: 0;
  background-image: var(--grain);
  opacity: .12;
  mix-blend-mode: overlay;
  pointer-events: none;
  z-index: 1000;
}
[data-testid="stHeader"] { background: transparent; }
[data-testid="stMainBlockContainer"] { max-width: 1100px; padding-top: 5rem; }

/* ---------- cards ---------- */
.st-key-profile_card, .st-key-feats_card {
  background: var(--surface);
  border: 1px solid var(--edge);
  border-radius: var(--radius);
  padding: 1.25rem;
}

/* ---------- portrait ---------- */
.pw-portrait {
  display: block;
  width: 100%;
  aspect-ratio: 3 / 4;
  object-fit: cover;
  border: 1px solid var(--edge-strong);
  border-radius: var(--radius);
}
.pw-portrait--empty {
  display: flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
  background: var(--raised);
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
}
div[data-baseweb="base-input"] { background: transparent !important; }
div[data-baseweb="input"]:focus-within {
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 1px var(--accent) !important;
}
.stApp input { color: var(--ink) !important; font-weight: 500; }
.stApp input::placeholder { color: var(--ink-faint) !important; font-weight: 400; }

[data-testid="stFileUploaderDropzone"] {
  background: var(--field);
  border-radius: var(--radius);
}
[data-testid="stToast"] { border-radius: var(--radius); }

/* ---------- buttons ---------- */
button:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }

[data-testid^="stBaseButton-secondary"] {
  background: var(--raised);
  border: 1px solid var(--edge-strong);
  border-radius: var(--radius);
  color: var(--ink);
  font-weight: 500;
}
[data-testid^="stBaseButton-secondary"]:hover {
  background: var(--raised-hover);
  border-color: var(--ink-faint);
  color: var(--ink);
}
[data-testid="stBaseButton-primary"] {
  background: var(--accent);
  border: 1px solid var(--accent);
  border-radius: var(--radius);
  color: #FFFFFF;
  font-weight: 600;
  padding: .55rem 1rem;
}
[data-testid="stBaseButton-primary"]:hover {
  background: var(--accent-hover);
  border-color: var(--accent-hover);
  color: #FFFFFF;
}

[data-testid="stPopoverBody"] {
  background: var(--surface);
  border: 1px solid var(--edge-strong);
  border-radius: var(--radius);
}

/* ---------- power-up chips ---------- */
.st-key-powerups_row {
  gap: .4rem;
  padding: .6rem;
  min-height: 3.2rem;
  background: var(--field);
  border: 1px solid var(--edge);
  border-radius: var(--radius);
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
}
.pw-empty {
  text-align: center;
  color: var(--ink-faint);
  font-size: .9rem;
  padding: 4rem 1rem;
}
[class*="st-key-feat_card_"] {
  background: var(--raised);
  border: 1px solid var(--edge);
  border-left: 3px solid var(--accent);
  border-radius: var(--radius);
  padding: .75rem 1rem;
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
  background: var(--accent);
  border: 1px solid var(--accent);
  color: #FFFFFF;
}
.st-key-feat_bar [data-testid="stFormSubmitButton"] button:hover {
  background: var(--accent-hover);
  border-color: var(--accent-hover);
  color: #FFFFFF;
}
"""


def inject_styles() -> None:
    """Apply the Power Scaling theme to the current page."""
    css = (_FONTS + _CSS).replace("__GRAIN__", _GRAIN)
    st.html(f"<style>{css}</style>")