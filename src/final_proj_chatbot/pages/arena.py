import base64
from dataclasses import dataclass, field
import html
import random
import time
from typing import Any
import urllib.parse

import altair as alt
import pandas as pd
import streamlit as st

from final_proj_chatbot.models.CharacterRepository import get_character_repo
from final_proj_chatbot.styles.style import inject_styles

st.set_page_config(
    page_title="Power Scaling - Arena",
    layout="wide",
)


# =============================================================================
# 1. LOW-TOKEN AI FIGHT PROTOCOL & PARSER
# =============================================================================

AI_FIGHT_PROMPT_TEMPLATE = """Simulate a power-scaling battle between Fighter 1 and Fighter 2.
Output ONLY compact pipe-delimited lines using this exact schema (no markdown, no JSON, no extra commentary):

T|<attacker:1|2|0>|<target:1|2|0>|<dmg:int>|<p1_pwr:int>|<p2_pwr:int>|<p1_spd:int>|<p2_spd:int>|<1-sentence narration>
R|<winner:1|2|0>|<short verdict title>|<2-3 sentence summary paragraph>

Rules:
- Emit 6 to 10 T lines in chronological order, ending with exactly 1 R line.
- attacker/target: 1=Fighter 1, 2=Fighter 2, 0=neutral/clash. Set dmg>0 whenever target takes a hit.
- p1_pwr & p2_pwr: dynamic energy/power output per turn (int).
- p1_spd & p2_spd: combat speed/tempo index from 1 to 100 (int).

Fighter 1: {f1_profile}
Fighter 2: {f2_profile}"""


def build_fight_prompt(fighter_1: Any, fighter_2: Any) -> str:
    """Format a compact LLM prompt instructing the AI to emit the low-token battle script."""
    def _summarize(c: Any) -> str:
        name = getattr(c, "name", "Unknown")
        origin = getattr(c, "origin", "Unknown")
        power_ups = ", ".join(getattr(c, "power_ups", []) or []) or "None"
        feats = "; ".join((getattr(c, "feats", []) or [])[:5]) or "None listed"
        return f"{name} ({origin}) | Power-ups: {power_ups} | Feats: {feats}"

    return AI_FIGHT_PROMPT_TEMPLATE.format(
        f1_profile=_summarize(fighter_1),
        f2_profile=_summarize(fighter_2),
    )


@dataclass
class FightEvent:
    turn: int
    attacker: int          # 1, 2, or 0
    target: int            # 1, 2, or 0
    damage: int
    p1_power: int
    p2_power: int
    p1_speed: int
    p2_speed: int
    narration: str


@dataclass
class FightResult:
    winner: int            # 1, 2, or 0 (draw)
    verdict: str
    summary: str


@dataclass
class FightSimulation:
    events: list[FightEvent] = field(default_factory=list)
    result: FightResult | None = None
    raw_script: str = ""


def _safe_int(val: str, default: int = 0) -> int:
    try:
        return int(float(val.strip()))
    except (ValueError, TypeError):
        return default


def parse_fight_script(raw_text: str, f1_name: str = "Fighter 1", f2_name: str = "Fighter 2") -> FightSimulation:
    """Parse low-token `T|...` and `R|...` lines emitted by the AI into structured telemetry."""
    events: list[FightEvent] = []
    result: FightResult | None = None

    for raw_line in raw_text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("```"):
            continue

        if line.startswith("T|"):
            parts = line.split("|", 8)
            if len(parts) < 9:
                continue
            events.append(
                FightEvent(
                    turn=len(events) + 1,
                    attacker=_safe_int(parts[1], 0),
                    target=_safe_int(parts[2], 0),
                    damage=max(0, _safe_int(parts[3], 0)),
                    p1_power=max(0, _safe_int(parts[4], 1000)),
                    p2_power=max(0, _safe_int(parts[5], 1000)),
                    p1_speed=max(1, min(100, _safe_int(parts[6], 50))),
                    p2_speed=max(1, min(100, _safe_int(parts[7], 50))),
                    narration=parts[8].strip(),
                )
            )
        elif line.startswith("R|"):
            parts = line.split("|", 3)
            if len(parts) >= 4:
                result = FightResult(
                    winner=_safe_int(parts[1], 0),
                    verdict=parts[2].strip(),
                    summary=parts[3].strip(),
                )

    # Fallback verdict if the AI omitted the R| line
    if result is None:
        f1_dmg = sum(e.damage for e in events if e.attacker == 1)
        f2_dmg = sum(e.damage for e in events if e.attacker == 2)
        if f1_dmg > f2_dmg:
            winner, verdict = 1, f"{f1_name} Dominates the Arena"
        elif f2_dmg > f1_dmg:
            winner, verdict = 2, f"{f2_name} Dominates the Arena"
        else:
            winner, verdict = 0, "Deadlocked Draw"
        summary = " ".join(e.narration for e in events)
        result = FightResult(winner=winner, verdict=verdict, summary=summary)

    return FightSimulation(events=events, result=result, raw_script=raw_text)


def _classify_energy_tier(peak_power: int) -> str:
    """Nerd destructive-capacity classification derived from peak energy output."""
    if peak_power >= 1_000_000:
        return "Planetary+"
    if peak_power >= 250_000:
        return "Continental"
    if peak_power >= 75_000:
        return "Island / Mountain"
    if peak_power >= 20_000:
        return "Multi-City Block"
    return "Street / Building"


# =============================================================================
# 2. SVG EMBLEM & FIGHTER CARD RENDERING (WITH REAL-TIME HIT SHAKE & RED GLOW)
# =============================================================================

def _vs_emblem_html(size_px: int = 120) -> str:
    """Render the brushstroke VS emblem as an encoded SVG <img>."""
    svg = (
        "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 140 140' fill='none'>"
        "<defs>"
        "<linearGradient id='vsGrad' x1='20' y1='20' x2='120' y2='120' gradientUnits='userSpaceOnUse'>"
        "<stop offset='0%' stop-color='#D92626'/>"
        "<stop offset='52%' stop-color='#FF551A'/>"
        "<stop offset='100%' stop-color='#FFB02E'/>"
        "</linearGradient>"
        "</defs>"
        "<path d='M24 30 L48 92 L78 24 L65 24 L48 67 L36 30 Z' "
        "fill='url(#vsGrad)' stroke='#F5F7FA' stroke-width='2.4' stroke-linejoin='round'/>"
        "<path d='M106 44 C94 36, 74 42, 74 56 C74 71, 108 68, 108 86 C108 102, 82 108, 64 98 "
        "L69 88 C82 95, 96 92, 96 85 C96 76, 62 78, 62 56 C62 38, 86 28, 111 36 Z' "
        "fill='url(#vsGrad)' stroke='#F5F7FA' stroke-width='2.4' stroke-linejoin='round'/>"
        "<path d='M34 112 L114 26 L106 24 L28 109 Z' fill='#FFFFFF' opacity='0.92'/>"
        "</svg>"
    )
    encoded = urllib.parse.quote(svg)
    return (
        f'<img class="pw-vs-img" src="data:image/svg+xml;utf8,{encoded}" '
        f'width="{size_px}" height="{size_px}" alt="VS" />'
    )


def _get_portrait_src(character: Any) -> str | None:
    for attr in ("portrait", "image", "image_url", "avatar", "photo"):
        val = getattr(character, attr, None)
        if not val:
            continue
        if isinstance(val, str):
            return val
        if isinstance(val, (bytes, bytearray)):
            encoded = base64.b64encode(val).decode("ascii")
            return f"data:image/png;base64,{encoded}"
    return None


def _get_character_scale(character: Any) -> str | int | float | None:
    for attr in ("scale", "tier", "power_tier", "level"):
        val = getattr(character, attr, None)
        if val is not None and str(val).strip() != "":
            return val
    return None


def _build_fighter_card_html(
    character: Any | None,
    side_label: str,
    active: bool = False,
    damaged: bool = False,
    damage_amount: int = 0,
    hit_seq: int = 0,
    show_plate: bool = False,
) -> str:
    """Build HTML for a fighter portrait card (with optional red shake damage state & nameplate)."""
    classes = ["pw-fighter-frame"]
    if active:
        classes.append("pw-fighter-frame--active")
    if damaged:
        variant = "a" if hit_seq % 2 == 0 else "b"
        classes.append(f"pw-fighter-frame--damaged-{variant}")

    frame_cls = " ".join(classes)

    if character is None:
        return (
            f'<div class="{frame_cls}">'
            f'<div class="pw-portrait pw-portrait--empty">Select {html.escape(side_label)}</div>'
            f"</div>"
        )

    src = _get_portrait_src(character)
    name = html.escape(str(getattr(character, "name", side_label)))
    origin = html.escape(str(getattr(character, "origin", "") or "Unknown Origin"))
    scale = _get_character_scale(character)
    scale_badge = f'<span class="pw-fighter-tag">{html.escape(str(scale))}</span>' if scale is not None else ""

    if src:
        portrait_html = f'<img class="pw-portrait" src="{html.escape(src, quote=True)}" alt="{name}" />'
    else:
        portrait_html = f'<div class="pw-portrait pw-portrait--empty">{name}</div>'

    damage_fx = ""
    if damaged:
        dmg_badge = f'<div class="pw-dmg-badge">-{damage_amount:,} DMG</div>' if damage_amount > 0 else ""
        damage_fx = f'<div class="pw-damage-overlay"></div>{dmg_badge}'

    plate_html = ""
    if show_plate:
        plate_cls = "pw-fighter-plate pw-fighter-plate--damaged" if damaged else "pw-fighter-plate"
        plate_html = f'<div class="{plate_cls}">{name}</div>'

    return (
        f'<div id="fighter-card-{html.escape(side_label)}-{hit_seq}" class="{frame_cls}">'
        f"{damage_fx}"
        f"{portrait_html}"
        f'<div class="pw-fighter-meta"><span>{origin}</span>{scale_badge}</div>'
        f"</div>"
        f"{plate_html}"
    )


# =============================================================================
# 3. NARRATION & REAL-TIME EVENT STREAMING
# =============================================================================

def _render_narration_box(lines: list[str]) -> str:
    if not lines:
        inner = '<div class="pw-narration-placeholder">Awaiting first clash...</div>'
    else:
        current_line = html.escape(lines[-1])
        previous = lines[:-1][-2:]

        items: list[str] = []
        for idx, old_text in enumerate(previous):
            is_oldest = len(previous) == 2 and idx == 0
            cls = "pw-narration-prev pw-narration-prev--faded" if is_oldest else "pw-narration-prev"
            items.append(f'<div class="{cls}">{html.escape(old_text)}</div>')

        history_html = f'<div class="pw-narration-history">{"".join(items)}</div>'
        inner = f'{history_html}<div class="pw-narration-current">{current_line}</div>'

    return f'<div class="pw-narration-box">{inner}</div>'


def _update_stage_slots(
    f1: Any,
    f2: Any,
    log: list[str],
    event: FightEvent | None = None,
    hit_seq: int = 0,
) -> None:
    """Update the narration stage and apply real-time shake/red glow to the damaged fighter."""
    narration_slot = st.session_state.get("_arena_narration_slot")
    f1_slot = st.session_state.get("_arena_f1_slot")
    f2_slot = st.session_state.get("_arena_f2_slot")

    f1_hit = bool(event and event.target == 1 and event.damage > 0)
    f2_hit = bool(event and event.target == 2 and event.damage > 0)

    if narration_slot is not None:
        narration_slot.html(_render_narration_box(log))

    if f1_slot is not None:
        f1_slot.html(
            _build_fighter_card_html(
                f1,
                side_label="f1",
                active=True,
                damaged=f1_hit,
                damage_amount=event.damage if f1_hit and event else 0,
                hit_seq=hit_seq,
                show_plate=True,
            )
        )

    if f2_slot is not None:
        f2_slot.html(
            _build_fighter_card_html(
                f2,
                side_label="f2",
                active=True,
                damaged=f2_hit,
                damage_amount=event.damage if f2_hit and event else 0,
                hit_seq=hit_seq,
                show_plate=True,
            )
        )


def _play_simulation(sim: FightSimulation, f1: Any, f2: Any) -> None:
    """Iterate through parsed FightEvents at 1s intervals with real-time card hit reactions."""
    log: list[str] = []
    st.session_state["arena_narration_log"] = log

    for idx, event in enumerate(sim.events):
        if idx > 0:
            time.sleep(1.0)
        log.append(event.narration)
        _update_stage_slots(f1, f2, log, event=event, hit_seq=idx + 1)

    # Brief pause on final blow before clearing hit glow and showing post-fight analytics
    time.sleep(0.85)
    _update_stage_slots(f1, f2, log, event=None, hit_seq=len(sim.events) + 1)
    st.session_state["arena_match_complete"] = True
    st.rerun()


# =============================================================================
# 4. FIGHT CALLBACK (DEMO GENERATOR USING THE LOW-TOKEN PROTOCOL)
# =============================================================================

def _generate_demo_ai_script(fighter_1: Any, fighter_2: Any) -> str:
    """Simulated AI output adhering to the low-token `T|...` and `R|...` protocol."""
    f1 = getattr(fighter_1, "name", "Fighter 1")
    f2 = getattr(fighter_2, "name", "Fighter 2")
    f1_powers = getattr(fighter_1, "power_ups", None) or ["Overdrive Aura"]
    f2_powers = getattr(fighter_2, "power_ups", None) or ["Phantom Surge"]
    p1_skill = random.choice(f1_powers)
    p2_skill = random.choice(f2_powers)

    # Randomized telemetry variance so Rematch produces distinct numbers & outcomes
    f1_wins = random.choice([True, False])
    b1 = random.randint(18000, 32000)
    b2 = random.randint(18000, 32000)

    if f1_wins:
        return "\n".join([
            f"T|0|0|0|{b1}|{b2}|74|76|{f1} and {f2} lock eyes as pressure fractures the arena gravel.",
            f"T|2|1|240|{int(b1*1.1)}|{int(b2*1.45)}|72|88|{f2} blitzes first with {p2_skill}, carving a shockwave across {f1}'s guard!",
            f"T|1|2|310|{int(b1*1.65)}|{int(b2*1.4)}|86|82|{f1} parries the follow-up and drives a heavy counter straight into {f2}'s ribs!",
            f"T|2|1|290|{int(b1*1.55)}|{int(b2*2.1)}|80|94|{f2} spikes energy output and slams {f1} through a pillar of debris!",
            f"T|1|2|460|{int(b1*2.65)}|{int(b2*1.95)}|95|85|{f1} ignites {p1_skill}, shattering {f2}'s defense with a blinding backdoor blow!",
            f"T|1|2|620|{int(b1*3.4)}|{int(b2*1.5)}|98|71|{f1} unleashes a full-output finisher that overwhelms {f2} across the arena floor!",
            f"R|1|{f1} Wins by Decisive Counter-Burst|After weathering {f2}'s early speed blitz, {f1} adapted mid-exchange and triggered {p1_skill} to flip momentum. {f1}'s peak power surge outscaled {f2}'s defensive threshold in the final two exchanges.",
        ])
    else:
        return "\n".join([
            f"T|0|0|0|{b1}|{b2}|75|75|{f1} and {f2} square off under the spotlight as static crackles in the air.",
            f"T|1|2|260|{int(b1*1.5)}|{int(b2*1.15)}|87|74|{f1} opens aggressively with {p1_skill}, landing a clean kinetic strike on {f2}!",
            f"T|2|1|340|{int(b1*1.4)}|{int(b2*1.8)}|81|91|{f2} slips inside {f1}'s reach and retaliates with a devastating {p2_skill} combo!",
            f"T|1|2|220|{int(b1*2.0)}|{int(b2*1.75)}|89|86|{f1} forces a high-speed exchange, grazing {f2} with a concentrated energy blast!",
            f"T|2|1|510|{int(b1*1.85)}|{int(b2*2.85)}|82|96|{f2} breaks past {f1}'s guard and detonates a point-blank shockwave!",
            f"T|2|1|640|{int(b1*1.45)}|{int(b2*3.5)}|70|99|{f2} channels maximum output into a final strike, dropping {f1} to one knee!",
            f"R|2|{f2} Wins by Relentless Tempo Escalation|Although {f1} claimed the opening exchange with {p1_skill}, {f2} maintained superior combat speed and continuously escalated output. {f2}'s late-match {p2_skill} surge overwhelmed {f1}'s recovery.",
        ])


def on_fight_start(fighter_1: Any, fighter_2: Any) -> None:
    """Callback triggered on FIGHT or REMATCH.

    Replace `_generate_demo_ai_script(...)` with your AI call using
    `prompt = build_fight_prompt(fighter_1, fighter_2)`.
    """
    f1_name = getattr(fighter_1, "name", "Fighter 1")
    f2_name = getattr(fighter_2, "name", "Fighter 2")

    # Future AI integration:
    # prompt = build_fight_prompt(fighter_1, fighter_2)
    # raw_ai_output = your_ai_module.generate(prompt)
    raw_ai_output = _generate_demo_ai_script(fighter_1, fighter_2)

    sim = parse_fight_script(raw_ai_output, f1_name=f1_name, f2_name=f2_name)
    st.session_state["arena_fight_sim"] = sim
    _play_simulation(sim, fighter_1, fighter_2)


# =============================================================================
# 5. POST-FIGHT SUMMARY & NERD TELEMETRY SECTION
# =============================================================================

def _render_post_fight_summary(sim: FightSimulation, fighter_1: Any, fighter_2: Any) -> None:
    """Render match verdict, nerd KPIs, interactive line charts, and full narration ledger."""
    if not sim.events:
        return

    f1_name = getattr(fighter_1, "name", "Fighter 1")
    f2_name = getattr(fighter_2, "name", "Fighter 2")
    primary_color = st.get_option("theme.primaryColor") or "#E0AA2D"
    f2_color = "#4EA8DE"

    # Compute nerd stats
    f1_dmg_total = sum(e.damage for e in sim.events if e.attacker == 1)
    f2_dmg_total = sum(e.damage for e in sim.events if e.attacker == 2)
    total_dmg = max(1, f1_dmg_total + f2_dmg_total)

    f1_hits = sum(1 for e in sim.events if e.attacker == 1 and e.damage > 0)
    f2_hits = sum(1 for e in sim.events if e.attacker == 2 and e.damage > 0)

    f1_peak_pwr = max(e.p1_power for e in sim.events)
    f2_peak_pwr = max(e.p2_power for e in sim.events)

    f1_avg_spd = round(sum(e.p1_speed for e in sim.events) / len(sim.events), 1)
    f2_avg_spd = round(sum(e.p2_speed for e in sim.events) / len(sim.events), 1)

    # Count momentum swings (lead changes in cumulative damage)
    cum1, cum2, prev_leader, swings = 0, 0, 0, 0
    rows: list[dict[str, Any]] = []
    for e in sim.events:
        if e.attacker == 1:
            cum1 += e.damage
        elif e.attacker == 2:
            cum2 += e.damage
        leader = 1 if cum1 > cum2 else (2 if cum2 > cum1 else prev_leader)
        if prev_leader != 0 and leader != prev_leader:
            swings += 1
        prev_leader = leader

        rows.append({
            "Turn": f"T{e.turn}",
            "TurnNum": e.turn,
            f"{f1_name} Power": e.p1_power,
            f"{f2_name} Power": e.p2_power,
            f"{f1_name} Cum. DMG": cum1,
            f"{f2_name} Cum. DMG": cum2,
            f"{f1_name} Tempo": e.p1_speed,
            f"{f2_name} Tempo": e.p2_speed,
        })

    df = pd.DataFrame(rows)

    # 1. Official Verdict & Summary Prose
    res = sim.result
    verdict_title = html.escape(res.verdict if res else "Match Concluded")
    summary_prose = html.escape(res.summary if res else " ".join(e.narration for e in sim.events))

    st.html(
        f"""
        <div class="pw-summary-banner">
          <div class="pw-summary-kicker">Official Arena Verdict &amp; Post-Match Analysis</div>
          <div class="pw-summary-verdict">{verdict_title}</div>
          <p class="pw-summary-prose">{summary_prose}</p>
        </div>
        """
    )

    st.markdown("<div style='height: 1rem'></div>", unsafe_allow_html=True)

    # 2. Nerd Telemetry KPI Strip
    k1, k2, k3, k4 = st.columns(4, gap="medium")
    with k1:
        f1_share = round((f1_dmg_total / total_dmg) * 100)
        st.html(
            f"""
            <div class="pw-kpi-card">
              <div class="pw-kpi-label">Total Damage Output</div>
              <div class="pw-kpi-value">{f1_dmg_total:,} vs {f2_dmg_total:,}</div>
              <div class="pw-kpi-sub">{html.escape(f1_name)} {f1_share}% &bull; {html.escape(f2_name)} {100 - f1_share}%</div>
            </div>
            """
        )
    with k2:
        top_pwr = max(f1_peak_pwr, f2_peak_pwr)
        st.html(
            f"""
            <div class="pw-kpi-card">
              <div class="pw-kpi-label">Peak Power Spike</div>
              <div class="pw-kpi-value">{f1_peak_pwr:,} vs {f2_peak_pwr:,}</div>
              <div class="pw-kpi-sub">Class: {_classify_energy_tier(top_pwr)}</div>
            </div>
            """
        )
    with k3:
        f1_dps = round(f1_dmg_total / max(1, f1_hits))
        f2_dps = round(f2_dmg_total / max(1, f2_hits))
        st.html(
            f"""
            <div class="pw-kpi-card">
              <div class="pw-kpi-label">Avg Damage / Strike</div>
              <div class="pw-kpi-value">{f1_dps:,} vs {f2_dps:,}</div>
              <div class="pw-kpi-sub">Tempo: {f1_avg_spd} vs {f2_avg_spd} idx</div>
            </div>
            """
        )
    with k4:
        st.html(
            f"""
            <div class="pw-kpi-card">
              <div class="pw-kpi-label">Combat Telemetry</div>
              <div class="pw-kpi-value">{len(sim.events)} Exchanges</div>
              <div class="pw-kpi-sub">Momentum Swings: {swings} &bull; Strikes: {f1_hits + f2_hits}</div>
            </div>
            """
        )

    st.markdown("<div style='height: 1rem'></div>", unsafe_allow_html=True)

    # 3. Interactive Line Graphs (Power Output, Cumulative Damage, Combat Tempo)
    def _build_line_chart(col_f1: str, col_f2: str, y_title: str) -> alt.Chart:
        melted = df.melt(
            id_vars=["Turn", "TurnNum"],
            value_vars=[col_f1, col_f2],
            var_name="Fighter",
            value_name="Value",
        )
        return (
            alt.Chart(melted)
            .mark_line(point=alt.OverlayMarkDef(size=70), strokeWidth=2.6)
            .encode(
                x=alt.X("Turn:N", sort=list(df["Turn"]), title="Battle Exchange"),
                y=alt.Y("Value:Q", title=y_title, scale=alt.Scale(zero=False)),
                color=alt.Color(
                    "Fighter:N",
                    scale=alt.Scale(domain=[col_f1, col_f2], range=[primary_color, f2_color]),
                    legend=alt.Legend(orient="top", title=None),
                ),
                tooltip=["Turn:N", "Fighter:N", alt.Tooltip("Value:Q", format=",")],
            )
            .properties(height=270)
            .configure(background="transparent")
            .configure_view(strokeWidth=0)
            .configure_axis(
                gridColor="rgba(255,255,255,0.08)",
                domainColor="rgba(255,255,255,0.18)",
                labelColor="#A3ABB8",
                titleColor="#A3ABB8",
            )
            .configure_legend(labelColor="#E4E8EE")
        )

    tab_pwr, tab_dmg, tab_spd, tab_log = st.tabs([
        "Power Output Curve",
        "Cumulative Damage Dealt",
        "Combat Speed & Tempo",
        "Full Battle Narration & Ledger",
    ])

    with tab_pwr:
        st.altair_chart(
            _build_line_chart(f"{f1_name} Power", f"{f2_name} Power", "Energy / Power Output"),
            use_container_width=True,
        )

    with tab_dmg:
        st.altair_chart(
            _build_line_chart(f"{f1_name} Cum. DMG", f"{f2_name} Cum. DMG", "Cumulative Damage Dealt"),
            use_container_width=True,
        )

    with tab_spd:
        st.altair_chart(
            _build_line_chart(f"{f1_name} Tempo", f"{f2_name} Tempo", "Combat Speed Index (1-100)"),
            use_container_width=True,
        )

    with tab_log:
        full_story = " ".join(e.narration for e in sim.events)
        st.markdown(f"**Complete Match Narration**\n\n{full_story}")
        st.markdown("---")
        for e in sim.events:
            hit_cls = "pw-log-row pw-log-row--hit" if e.damage > 0 else "pw-log-row"
            if e.target == 1 and e.damage > 0:
                dmg_tag = f'<span class="pw-log-dmg">-{e.damage:,} DMG &rarr; {html.escape(f1_name)}</span>'
            elif e.target == 2 and e.damage > 0:
                dmg_tag = f'<span class="pw-log-dmg">-{e.damage:,} DMG &rarr; {html.escape(f2_name)}</span>'
            else:
                dmg_tag = "<span>Clash / Positioning</span>"

            st.html(
                f"""
                <div class="{hit_cls}">
                  <div>
                    <div class="pw-log-turn">Exchange {e.turn:02d}</div>
                    <div class="pw-log-text">{html.escape(e.narration)}</div>
                  </div>
                  <div class="pw-log-metrics">
                    {dmg_tag}<br/>
                    <span>PWR {e.p1_power:,} / {e.p2_power:,}</span>
                  </div>
                </div>
                """
            )


# =============================================================================
# 6. PAGE STATE & LAYOUT
# =============================================================================

def _init_arena_state() -> None:
    st.session_state.setdefault("arena_fighting", False)
    st.session_state.setdefault("arena_run_mode", None)      # "rematch" | "replay" | None
    st.session_state.setdefault("arena_match_complete", False)
    st.session_state.setdefault("arena_fight_sim", None)
    st.session_state.setdefault("arena_narration_log", [])
    st.session_state.setdefault("arena_f1_id", None)
    st.session_state.setdefault("arena_f2_id", None)


def render_arena() -> None:
    _init_arena_state()

    repo = get_character_repo()
    characters = repo.get_all()

    char_by_id = {c.id: c for c in characters}
    f1 = char_by_id.get(st.session_state["arena_f1_id"])
    f2 = char_by_id.get(st.session_state["arena_f2_id"])

    active_scale = _get_character_scale(f1) or _get_character_scale(f2)
    inject_styles(scale=active_scale)

    if not characters:
        st.info("Loading fighters from LocalStorage — or create at least two fighters first to enter the Arena.")
        return

    ids = [c.id for c in characters]
    if st.session_state["arena_f1_id"] not in char_by_id:
        st.session_state["arena_f1_id"] = ids[0]
    if st.session_state["arena_f2_id"] not in char_by_id:
        st.session_state["arena_f2_id"] = ids[1] if len(ids) > 1 else ids[0]

    f1 = char_by_id.get(st.session_state["arena_f1_id"])
    f2 = char_by_id.get(st.session_state["arena_f2_id"])
    is_fighting: bool = st.session_state["arena_fighting"]

    # =========================================================================
    # VIEW 1: PRE-FIGHT LOBBY
    # =========================================================================
    if not is_fighting:
        with st.container(key="arena_lobby_view"):
            col_left, col_center, col_right = st.columns([1.15, 0.85, 1.15], gap="large")

            with col_left:
                st.html(_build_fighter_card_html(f1, side_label="Fighter 1", active=False))
                st.markdown("<div style='height: 0.6rem'></div>", unsafe_allow_html=True)
                selected_f1 = st.selectbox(
                    "Fighter 1",
                    options=ids,
                    index=ids.index(st.session_state["arena_f1_id"]),
                    format_func=lambda cid: char_by_id[cid].name,
                    key="arena_select_f1",
                    label_visibility="collapsed",
                )
                if selected_f1 != st.session_state["arena_f1_id"]:
                    st.session_state["arena_f1_id"] = selected_f1
                    st.rerun()

            with col_right:
                st.html(_build_fighter_card_html(f2, side_label="Fighter 2", active=False))
                st.markdown("<div style='height: 0.6rem'></div>", unsafe_allow_html=True)
                selected_f2 = st.selectbox(
                    "Fighter 2",
                    options=ids,
                    index=ids.index(st.session_state["arena_f2_id"]),
                    format_func=lambda cid: char_by_id[cid].name,
                    key="arena_select_f2",
                    label_visibility="collapsed",
                )
                if selected_f2 != st.session_state["arena_f2_id"]:
                    st.session_state["arena_f2_id"] = selected_f2
                    st.rerun()

            with col_center:
                st.html(f'<div class="pw-vs-wrap pw-vs-wrap--lobby">{_vs_emblem_html(126)}</div>')

                same_fighter = st.session_state["arena_f1_id"] == st.session_state["arena_f2_id"]
                with st.container(key="fight_btn_wrap"):
                    fight_clicked = st.button(
                        "FIGHT",
                        type="primary",
                        use_container_width=True,
                        disabled=same_fighter or len(characters) < 2,
                    )

                if len(characters) < 2:
                    st.caption("Create at least 2 characters to start a match.")
                elif same_fighter:
                    st.caption("Select two different fighters.")

                if fight_clicked and f1 and f2:
                    st.session_state["arena_fighting"] = True
                    st.session_state["arena_run_mode"] = "rematch"
                    st.session_state["arena_match_complete"] = False
                    st.session_state["arena_narration_log"] = []
                    st.rerun()

    # =========================================================================
    # VIEW 2: IN-FIGHT NARRATION STAGE + POST-FIGHT SUMMARY
    # =========================================================================
    else:
        with st.container(key="arena_battle_view"):
            col_left, col_center, col_right = st.columns([0.95, 1.5, 0.95], gap="large")

            with col_left:
                f1_slot = st.empty()
                st.session_state["_arena_f1_slot"] = f1_slot
                f1_slot.html(_build_fighter_card_html(f1, side_label="f1", active=True, show_plate=True))

            with col_center:
                st.html(f'<div class="pw-vs-wrap pw-vs-wrap--crown">{_vs_emblem_html(64)}</div>')
                narration_slot = st.empty()
                st.session_state["_arena_narration_slot"] = narration_slot
                narration_slot.html(_render_narration_box(st.session_state["arena_narration_log"]))

                st.markdown("<div style='height: 0.75rem'></div>", unsafe_allow_html=True)
                btn_replay, btn_rematch, btn_stop = st.columns(3, gap="small")

                with btn_replay:
                    if st.button(
                        "Replay",
                        use_container_width=True,
                        disabled=st.session_state["arena_fight_sim"] is None,
                    ):
                        st.session_state["arena_run_mode"] = "replay"
                        st.session_state["arena_match_complete"] = False
                        st.session_state["arena_narration_log"] = []
                        st.rerun()

                with btn_rematch:
                    if st.button("Rematch", type="primary", use_container_width=True):
                        st.session_state["arena_run_mode"] = "rematch"
                        st.session_state["arena_match_complete"] = False
                        st.session_state["arena_narration_log"] = []
                        st.rerun()

                with btn_stop:
                    if st.button("Stop Match", use_container_width=True):
                        st.session_state["arena_fighting"] = False
                        st.session_state["arena_run_mode"] = None
                        st.session_state["arena_match_complete"] = False
                        st.session_state["arena_narration_log"] = []
                        st.rerun()

            with col_right:
                f2_slot = st.empty()
                st.session_state["_arena_f2_slot"] = f2_slot
                f2_slot.html(_build_fighter_card_html(f2, side_label="f2", active=True, show_plate=True))

        # Execute live simulation (either fresh AI generation on Rematch, or cached Replay)
        run_mode = st.session_state.pop("arena_run_mode", None)
        if run_mode == "rematch" and f1 and f2:
            on_fight_start(f1, f2)
        elif run_mode == "replay" and f1 and f2:
            cached_sim: FightSimulation | None = st.session_state.get("arena_fight_sim")
            if cached_sim is not None:
                _play_simulation(cached_sim, f1, f2)

        # Render post-fight verdict, nerd telemetry KPIs, and line graphs once narration completes
        if st.session_state.get("arena_match_complete") and st.session_state.get("arena_fight_sim") and f1 and f2:
            _render_post_fight_summary(st.session_state["arena_fight_sim"], f1, f2)


render_arena()