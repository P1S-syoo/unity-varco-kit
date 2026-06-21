---
name: unity-ugui-layout
description: >-
  Build clean, good-looking Unity uGUI game UI from code (editor builders or runtime MonoBehaviours)
  instead of hand-placing ugly hardcoded layouts. Use this whenever working on Unity UI/HUD/panels/menus —
  designing or refactoring a HUD, dialog, popup, minigame UI, gauge, or score display; centralizing a
  UITheme/design-token file; fixing "engineer-made ugly UI" (overlapping elements, no font hierarchy,
  flat panels, Korean/CJK text showing as tofu □, absolute-coordinate spaghetti); or applying anchors,
  LayoutGroups, 9-slice, golden-ratio panels, glassmorphism, or DOTween UI motion. Trigger even if the
  user just says "the UI looks bad / make it prettier / lay out the HUD" without naming these techniques.
---

# Unity uGUI Layout & Design (code-built UI)

## Why code-built UI gets ugly (and how this skill fixes it)

When UI is generated from code — editor "builder" scripts or runtime `MonoBehaviour`s that
`AddComponent` their own Canvas/panels — engineers reach for **hardcoded pixel coordinates**,
**one font size everywhere**, and **flat single-color panels**. The result reads as
"made by a programmer": elements overlap at other resolutions, nothing has visual hierarchy,
and CJK text silently renders as tofu (□) because the runtime font was never assigned.

None of that is a talent problem — it's a **missing design-token layer + missing layout automation**.
Fix the system, not each screen. The payoff: change a handful of tokens and *every* screen improves at once.

This skill is framework-grounded in **Unity uGUI + TextMeshPro + DOTween**, the common code-built-UI stack.

## The core workflow

Apply these in order. Each step references the catalog in `references/token-and-helper-catalog.md`
(read it for concrete token values and helper signatures) and font specifics in
`references/korean-font-and-pitfalls.md`.

### 1. Centralize design tokens (the single most important step)
Put every color, font size, spacing, and elevation value in **one static `UITheme` class**.
Builders and runtime UI read tokens only — never inline `new Color(...)` or magic `fontSize = 15`.
This is what makes a later restyle a one-file change instead of a scavenger hunt.

- **Color: 60/30/10.** Dominant background (60%), supporting panel (30%), one glowing accent (10%,
  reserved for interaction/CTA only). Reserve semantic colors (danger/warn/success/info) and don't
  spend the accent on chrome. A palette that "feels off" is usually one stray hue (e.g. a generic
  purple in an otherwise teal scheme) or 6 saturated colors fighting on one screen — cut to ≤3.
- **Dark-theme depth = brightness, not shadow.** On dark UI, drop shadows vanish. Express elevation
  by making nearer surfaces *lighter*: bg `#08111C` → panel `#0F2030` → modal `#162A40`. If your
  background and panel sit at ~1.7:1 contrast they look flat — widen it.
- **Type hierarchy with real steps.** Display / Title / Heading / Body / Caption + a big **Metric**
  size for numbers (HP, score, depth) in Bold. If everything is within a few px it reads as one
  flat level. Make gameplay numbers large; labels small.
- **8pt spacing grid.** All padding/spacing from `{4,8,16,24,32,48}` constants. Parent padding ≥
  child spacing. Kills the "random gaps" look and avoids sub-pixel blur (also: keep RectTransform
  values integer).

### 2. Build through helpers, not raw coordinates
Give `UITheme` factory helpers (`MakePanel`, `MakeText`, `MakeButton`, `MakeGauge`, …) and have
all builders call those. Centralizes font application, rounding, raycast settings, and styling so
no screen can drift. Keep helper signatures stable so existing call sites don't break when you restyle.

### 3. Automate layout — stop hand-placing repeated elements
Any **list/grid/repeated row** (inventory, recipe rows, resource readouts) → `VerticalLayoutGroup`/
`HorizontalLayoutGroup`/`GridLayoutGroup` + `ContentSizeFitter` (+ `LayoutElement` for per-item sizing).
Hand-tuned `anchoredPosition` per row breaks the moment text length changes at runtime. Reserve manual
anchors for a few fixed singletons. Set `CanvasScaler` to **Scale With Screen Size, 1920×1080, Match 0.5**
on every canvas (never Constant Pixel Size), and wrap roots in a Safe Area container for notches.

### 4. Give panels depth (9-slice + glass)
Crisp scalable panels/buttons use **9-slice** sprites (`Image.type = Sliced`) so corners never
distort. Layer a translucent "glass" surface (semi-transparent fill + 1px accent border + a faint
top highlight) for a modern look. Note: uGUI has no real backdrop blur — "glass" here is
translucency + border + highlight, and if you stack an opaque base under it for text contrast you've
mostly cancelled the translucency, so pick one. Set `raycastTarget = false` on decorative Images so
they don't eat clicks.

### 5. Put motion where it's *felt*, not just on open
The motion that sells a game UI is **gameplay feedback**, not popup fades: gauges easing to their new
value, a number punching on gain, a danger gauge pulsing. Tween `fillAmount` (don't snap it). Keep
punches subtle (low vibrato/elasticity) — default DOTween punch is too violent. For entrances, a
"rise + fade" (translateY +20→0, ease-out ~0.25s) reads well. **Always** `Kill` a target's tweens
before starting a new one and in `OnDisable`/`OnDestroy`, or you get drift and "tween on destroyed
object" errors. (See the RiseIn ordering note in the catalog — capture the settle position *after*
killing, never before.)

### 6. Make fonts bulletproof (CJK/Korean = no tofu □)
This is the #1 silent bug in code-built UI. See `references/korean-font-and-pitfalls.md` for the full
pipeline, but the essence: `UITheme.UIFont` set only by *editor* builders is **null at runtime**, so
runtime-built text falls back to the default Latin font → CJK renders as □. Fix with (a) a
`[DefaultExecutionOrder(-1000)]` MonoBehaviour that injects the font static in `Awake` before any UI
builds, (b) a `ResolveFont()` fallback to `TMP_Settings.defaultFontAsset`, and (c) a CJK font set as
the TMP **default** with a fallback font for missing glyphs (so stray chars like `—` never tofu).
Use **Dynamic SDF** atlas mode for CJK (11k+ glyphs rasterize on demand; static would explode).

### 7. No-overlap placement + golden-ratio panels
For HUDs, place readouts in the **four screen corners** with a fixed safe margin and fixed block size,
then verify the math that opposite blocks can't collide at the reference resolution; push banners/toasts
into the vertical gaps. For focal popups, size them to the **golden ratio (1.618:1)** — it just looks
composed. A modal dialog should feel *focused*: dim the rest of the screen with a raycast-blocking
backdrop rather than letting it visually overlap the HUD.

## Anti-pattern → fix quick reference

| Smell | Fix |
|---|---|
| Hardcoded `new Color`, magic `fontSize` everywhere | One `UITheme` token class; read tokens only |
| Absolute `anchoredPosition` per repeated row | LayoutGroup + ContentSizeFitter |
| Constant Pixel Size canvas | Scale With Screen Size 1920×1080 Match 0.5 |
| 6 saturated colors / one stray hue | 60/30/10, ≤3 on screen, cut the outlier |
| Everything one font size | Display/Title/Heading/Body/Caption + big Bold Metric |
| Flat dark panels (shadow invisible) | Elevation via brightness steps |
| Gauge snaps to value | Tween `fillAmount` (OutCubic ~0.3s) |
| CJK text shows as □ | Runtime font binder + TMP default + fallback (Dynamic SDF) |
| Decorative image blocks clicks | `raycastTarget = false` |
| Panel/button corners stretch when resized | 9-slice `Image.type = Sliced` |
| Elements overlap at other resolutions | Corner placement + safe margin + verify collision math |
| Popups feel arbitrary; overlap HUD | Golden-ratio size + dim backdrop = focused modal |

## How to apply on an existing project
1. **Find or create the token hub** (`UITheme` or equivalent) and audit it against §1. Most wins are here.
2. **Read the builders/runtime UI** and list smells from the table above with file:line.
3. **Fix tokens first, rebuild, look.** Then structure (LayoutGroups, 9-slice, scaler), then detail
   (glass, motion, font safety, no-overlap/golden-ratio).
4. **Keep game/logic code untouched** — restyle is a separate pass from behavior. Verify visually
   (live play, since editor-mode and play-mode captures are unreliable for runtime-router HUDs).
5. Watch for the classic traps: DOTween *UI-module* shortcuts (`DOFillAmount`/`DOColor`/`DOFade`) may
   not be linked in a game asmdef — use core `DOTween.To(getter, setter, target, dur)` instead;
   `[RuntimeInitializeOnLoadMethod]` can't load project assets (use a serialized MonoBehaviour ref);
   and never trust that a "wired" field actually renders — confirm in play.

Read `references/token-and-helper-catalog.md` for concrete token values, helper signatures, and the
golden-ratio / no-overlap math, and `references/korean-font-and-pitfalls.md` for the font pipeline.
