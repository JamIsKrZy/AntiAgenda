# Arena Fight Generation Protocol & AI Prompt Guide

This document defines the **low-token pipe-delimited output format** required by `arena.py` (`parse_fight_script`). By avoiding JSON keys, braces, and verbose markdown, this schema cuts token consumption by **~65%** while driving real-time card hit animations and post-match telemetry graphs.

---

## 1. Ready-to-Use AI Prompt Template

Use the following prompt when calling your LLM module. Inject the formatted character sheets into `{f1_profile}` and `{f2_profile}`:

```text
You are the Arena Combat Engine & Power-Scaling Narrator. Simulate a logical, dramatic battle between Fighter 1 and Fighter 2 based on their origins, power-ups, and feats.

Output ONLY compact pipe-delimited lines using this exact schema (NO markdown blocks, NO JSON, NO intro/outro text):

T|<attacker:1|2|0>|<target:1|2|0>|<dmg:int>|<p1_pwr:int>|<p2_pwr:int>|<p1_spd:int>|<p2_spd:int>|<1-sentence narration>
R|<winner:1|2|0>|<short verdict title>|<2-3 sentence summary paragraph>

STRICT RULES:
1. Emit 6 to 10 `T|` lines in chronological order, followed by 1 `R|` line at the very end.
2. `attacker` and `target`: `1` = Fighter 1, `2` = Fighter 2, `0` = neutral/clash/dodged.
3. `dmg`: Integer >= 0. Set `dmg > 0` ONLY when `target` is `1` or `2` and takes a direct hit. Set `dmg = 0` when `target = 0` (clashes, parries, or positioning).
4. `p1_pwr` and `p2_pwr`: Positive integers representing instantaneous energy/power output on that turn. Scale numbers to match their feats (see Energy Tiers).
5. `p1_spd` and `p2_spd`: Integers from `1` to `100` representing combat speed/tempo on that turn.
6. Narration (`T|` last field): Exactly 1 punchy, vivid sentence (max 22 words). Reference their actual power-ups and feats.
7. Verdict (`R|` line): `winner` must match the fighter who dominated the decisive exchanges (`0` only for a true stalemate).

Fighter 1: {f1_profile}
Fighter 2: {f2_profile}
```

### Recommended Fighter Profile Input Format
Pass each fighter's `Character` fields in a single compact line to save input tokens:
```text
{name} ({origin}) | Power-ups: {comma_separated_power_ups} | Feats: {semicolon_separated_feats}
```

---

## 2. Line-by-Line Schema Reference

The parser reads the AI response line-by-line, ignoring blank lines. Every non-empty line **must** start with either `T|` or `R|`.

### A. Combat Turn Event (`T|...`)
`T|<attacker>|<target>|<dmg>|<p1_pwr>|<p2_pwr>|<p1_spd>|<p2_spd>|<narration>`

| Index | Field | Type / Values | UI & Telemetry Effect in `arena.py` |
| :--- | :--- | :--- | :--- |
| `0` | Record Type | Literal `T` | Identifies a chronological battle exchange (`Turn 1..N`). |
| `1` | `attacker` | `1`, `2`, or `0` | Credits cumulative damage dealt (`1` = Fighter 1, `2` = Fighter 2, `0` = neutral). |
| `2` | `target` | `1`, `2`, or `0` | Selects which portrait card receives impact FX (`1` = Left, `2` = Right, `0` = None). |
| `3` | `dmg` | Integer ($\ge 0$) | When `target` is `1` or `2` and `dmg > 0`, triggers the **card shake, crimson glow, and `-{dmg} DMG` badge**. Also plots the **Cumulative Damage** chart. |
| `4` | `p1_pwr` | Integer ($\ge 0$) | Fighter 1's energy output this turn. Plots **Power Output Curve** & **Peak Power Spike**. |
| `5` | `p2_pwr` | Integer ($\ge 0$) | Fighter 2's energy output this turn. Plots **Power Output Curve** & **Peak Power Spike**. |
| `6` | `p1_spd` | Integer ($1\text{–}100$) | Fighter 1's combat tempo/speed index this turn. Plots **Combat Speed & Tempo**. |
| `7` | `p2_spd` | Integer ($1\text{–}100$) | Fighter 2's combat tempo/speed index this turn. Plots **Combat Speed & Tempo**. |
| `8` | `narration` | String | Displayed enlarged in the center arena stage for 1 second, then shifted upward as dimmed history. |

### B. Match Result Verdict (`R|...`)
`R|<winner>|<verdict>|<summary>`

| Index | Field | Type / Values | UI & Telemetry Effect in `arena.py` |
| :--- | :--- | :--- | :--- |
| `0` | Record Type | Literal `R` | Marks the final match outcome (must appear once at the end). |
| `1` | `winner` | `1`, `2`, or `0` | `1` = Fighter 1 victory, `2` = Fighter 2 victory, `0` = Draw. |
| `2` | `verdict` | Short Title | Rendered as the bold headline in the post-match banner (e.g., `Goku Wins by Decisive Counter-Burst`). |
| `3` | `summary` | 2–3 Sentences | Rendered as the analytical post-match breakdown paragraph below the verdict title. |

---

## 3. Power-Scaling & Telemetry Calibration

To make the post-match nerd statistics and line graphs meaningful, instruct or tune the AI to follow these numeric ranges:

### Destructive Capacity / Power Output (`p1_pwr`, `p2_pwr`)
`arena.py` automatically classifies the highest `p1_pwr` or `p2_pwr` value in the match into an Energy Tier badge:

| Peak Power Output (`p1_pwr` / `p2_pwr`) | Arena Telemetry Classification | Example Character Tier |
| :--- | :--- | :--- |
| `< 20,000` | **Street / Building** | Peak humans, martial artists, street vigilantes |
| `20,000 – 74,999` | **Multi-City Block** | City-block busters, heavy mecha, enhanced superhumans |
| `75,000 – 249,999` | **Island / Mountain** | Mountain-levelers, high-tier elementalists |
| `250,000 – 999,999` | **Continental** | Country/continent-scale threats |
| `>= 1,000,000` | **Planetary+** | Planet-busters, stellar, galaxy, and cosmic entities |

* **Dynamic Curves**: Power output should rise as fighters activate transformations or `power_ups`, and dip when a fighter takes heavy damage or exhausts stamina.

### Damage & Momentum Rules (`dmg`)
* **Opening / Stalemate Turns**: Use `T|0|0|0|...` on Turn 1 (and mid-fight beam struggles/parries) so `dmg` is `0` and neither card flashes red prematurely.
* **Standard Hits**: `150 – 350` damage.
* **Signature Power-Up / Counter Hits**: `350 – 550` damage.
* **Finisher / Ultimate Blow**: `550 – 850` damage.
* **Momentum Swings**: The post-match KPI counts how many times the cumulative damage leader changes. Having the losing fighter take an early lead before the winner rallies creates dramatic telemetry.

### Combat Tempo (`p1_spd`, `p2_spd`)
* Keep values between `1` and `100`.
* Speed-blitz fighters should spike into `90–99` during rush turns, while stunned or recovering fighters drop to `60–75`.

---

## 4. Formatting Guardrails (Do's & Don'ts)

* **DO** keep each `T|` narration sentence concise (**12–22 words**, under ~140 characters) so it reads cleanly inside the center stage box in 1-second intervals.
* **DO** ensure `target` and `dmg` agree: if `dmg > 0`, `target` **must** be `1` or `2`.
* **DO NOT** wrap the response in ` ```text ` or ` ``` ` code fences (the parser skips fences, but omitting them saves tokens).
* **DO NOT** use the pipe character (`|`) inside the verdict title or narration text.
* **DO NOT** output more than 10 `T|` lines, as the live simulation plays at 1 second per turn (`6–8` turns = ideal `6–8s` pacing).

---

## 5. Complete Valid Example Output

```text
T|0|0|0|420000|390000|84|82|Goku and Rem step into the spotlight as static pressure cracks the arena gravel.
T|2|1|260|410000|540000|80|93|Rem vanishes into shadow-step and slices across Goku's guard with a crescent astral strike!
T|1|2|310|680000|510000|91|85|Goku flares Super Saiyan aura, parrying Rem's follow-up and landing a heavy gut punch!
T|0|0|0|790000|770000|94|94|Both fighters collide mid-air in a blinding shockwave that tears craters across the stage!
T|2|1|440|720000|960000|83|97|Rem invokes Lunar Eclipse, binding Goku's movement and detonating a point-blank gravity burst!
T|1|2|520|1250000|880000|99|86|Goku breaks through with Ultra Instinct, blitzing past Rem's blind spot with a devastating counter!
T|1|2|690|1480000|610000|98|72|Goku fires a point-blank Kamehameha that overwhelms Rem's barrier and decides the match!
R|1|Goku Wins by Ultra Instinct Counter-Burst|After absorbing Rem's mid-match Lunar Eclipse offensive, Goku triggered Ultra Instinct to surpass Rem's peak speed threshold. Goku's final two energy spikes outscaled Rem's defensive output and flipped cumulative damage in the closing exchanges.
```