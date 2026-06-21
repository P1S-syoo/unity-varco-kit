# UITheme token & helper catalog

Concrete, battle-tested values and helper shapes for a code-built Unity uGUI design system.
Adapt names/values to the project; the *structure* is the reusable part. All examples are C#
for a static `UITheme` class plus factory helpers.

## Table of contents
- [Color tokens](#color-tokens)
- [Typography tokens](#typography-tokens)
- [Spacing & elevation tokens](#spacing--elevation-tokens)
- [Factory helper signatures](#factory-helper-signatures)
- [Golden-ratio sizing](#golden-ratio-sizing)
- [No-overlap corner placement](#no-overlap-corner-placement)
- [Gauge fill tween](#gauge-fill-tween)
- [Rise-in entrance (kill-order gotcha)](#rise-in-entrance-kill-order-gotcha)
- [Glass panel](#glass-panel)
- [Button scale feedback](#button-scale-feedback)

## Color tokens
A dark underwater/teal example palette (swap hues for your game, keep the 4-layer + 60/30/10 shape):

```csharp
// 60% background, 30% panel, 10% accent — accent reserved for interaction/CTA only
public static readonly Color BgDeep   = Hex("#08111C"); // Elevation 0 — screen background
public static readonly Color BgPanel  = Hex("#0F2030"); // Elevation 1 — cards/panels (lighter than bg!)
public static readonly Color BgModal  = Hex("#162A40"); // Elevation 2 — modals/dropdowns
public static readonly Color BgHeader = Hex("#0A1622"); // darker strip — gauge tracks, headers
public static readonly Color Accent   = Hex("#00E5CC"); // glowing aqua — 10%, interaction only

public static readonly Color ColDanger  = Hex("#FF4D4D"); // HP/critical
public static readonly Color ColWarn     = Hex("#FFB347"); // caution
public static readonly Color ColSuccess  = Hex("#7AFF8C"); // pickup/clear
public static readonly Color ColInfo     = Hex("#00E5CC"); // oxygen/info

public static readonly Color TextPrimary   = Hex("#E8F1F5"); // slight tint > pure white reduces eye strain
public static readonly Color TextSecondary = Hex("#93AAB8");

// Glass surface
public static readonly Color GlassFill      = new Color(0f, 0.11f, 0.20f, 0.60f);
public static readonly Color GlassBorder    = new Color(0f, 0.90f, 0.80f, 0.18f); // aqua, low alpha
public static readonly Color GlassHighlight = new Color(1f, 1f, 1f, 0.10f);       // top sheen
```

Rules: never inline `new Color` in builders — add a token. Keep ≤3 saturated colors visible at once.
If a hue clashes with the scheme (e.g. a default purple), recolor it into the family.

## Typography tokens
Bias **larger** than feels necessary on first pass — code UI almost always ends up too small.

```csharp
public const float FontDisplay = 56f; // hero / title screen
public const float FontTitle   = 40f; // panel titles
public const float FontHeading = 28f; // section headers
public const float FontBody    = 22f; // normal text (don't go below ~16)
public const float FontCaption = 17f; // labels, hints
public const float FontMetric  = 40f; // gameplay numbers (HP/score/depth), use Bold
public const FontStyles MetricStyle  = FontStyles.Bold;
```

For numeric readouts use a **tabular (monospaced-digit)** font feature so the layout doesn't jitter
as digits change. Put the unit one tier smaller than the number.

## Spacing & elevation tokens
```csharp
public const float SpaceXS = 4f, SpaceSM = 8f, SpaceMD = 16f, SpaceLG = 24f, SpaceXL = 32f, SpaceXXL = 48f;
public const float GaugeHeight = 14f;             // thin gauges read poorly; 14+ is legible
public static RectOffset PanelPad(int p) => new RectOffset(p, p, p, p);
```

## Factory helper signatures
Keep these signatures stable across restyles. Each helper applies tokens + font + rounding internally.

```csharp
static Image            MakePanel(string name, Transform parent, Vector2 aMin, Vector2 aMax,
                                  Vector2 offMin, Vector2 offMax, Color color);
static Image            MakeGlassPanel(string name, Transform parent, Vector2 aMin, Vector2 aMax,
                                  Vector2 offMin, Vector2 offMax);             // fill+border+highlight
static TMP_Text         MakeText(string name, Transform parent, string content, float size,
                                  Color color, TextAlignmentOptions align);   // calls ApplyFont!
static Button           MakeButton(string name, Transform parent, string label, float size,
                                  Vector2 anchoredPos, Vector2 sizeDelta, Color bg);
static Image            MakeGauge(...);            // track = BgHeader (dark) so fill stands out
static void             AddVerticalLayout(GameObject go, float spacing, int pad); // +ContentSizeFitter
static void             AddScaleFeedback(Button b, float hover, float press);
static void             TweenFill(Image fill, float target, float dur = 0.3f);
static void             RiseIn(GameObject go, float dist = 20f, float dur = 0.25f);
static Vector2          GoldenSize(float longSide, bool widthIsLong);
static void             ApplyFont(TMP_Text t);     // t.font = ResolveFont(); (see font reference)
```

## Golden-ratio sizing
```csharp
public const float Golden = 1.618f;
public static Vector2 GoldenSize(float longSide, bool widthIsLong) {
    float shortSide = longSide / Golden;
    return widthIsLong ? new Vector2(longSide, shortSide) : new Vector2(shortSide, longSide);
}
// e.g. a craft popup: GoldenSize(1300f, true) => 1300 x 803
```
This sizes the *outer box*; it does not enforce internal golden division — lay out contents normally.

## No-overlap corner placement
Place HUD readouts in 4 corners with a fixed safe margin and fixed block size, then *prove* opposite
blocks can't collide at the reference resolution.

```csharp
const float HUD_SAFE = 32f, HUD_BLOCK_W = 320f, HUD_BLOCK_H = 96f;
// corner: 0=TL 1=TR 2=BL 3=BR. Anchor to the corner, offset inward by HUD_SAFE.
// Collision check @1920x1080: left blocks span x[32..352], right blocks x[1568..1888] -> 1216px gap. OK.
// Warning banner / toast go in the vertical gap BELOW the top blocks (y below -(HUD_SAFE+HUD_BLOCK_H)).
```
If a readout must sit centrally (e.g. a depth band), give it its own lane (e.g. left edge, y 20%–80%)
that the corner blocks don't enter, and verify numerically.

## Gauge fill tween
Use **core** DOTween (UI-module shortcuts like `DOFillAmount` may be unlinked in a game asmdef):
```csharp
public static void TweenFill(Image fill, float target, float dur = 0.3f) {
    if (fill == null) return;
    DOTween.Kill(fill);
    target = Mathf.Clamp01(target);
    try {
        DOTween.To(() => fill.fillAmount, v => fill.fillAmount = v, target, dur)
               .SetEase(Ease.OutCubic).SetUpdate(true).SetTarget(fill);
    } catch { fill.fillAmount = target; } // safe fallback
}
```
**Gauge not moving?** Confirm the Image is `Image.type = Filled` with a `fillMethod` set, and that the
bar you're animating is the *fill* image (not the track), and that the value source actually changes.
A common bug: the % label is wired to data but the bar Image's `fillAmount` is never written (or is
written on the wrong Image).

## Rise-in entrance (kill-order gotcha)
```csharp
public static void RiseIn(GameObject go, float dist = 20f, float dur = 0.25f) {
    var rt = go.GetComponent<RectTransform>();
    var cg = go.GetComponent<CanvasGroup>() ?? go.AddComponent<CanvasGroup>();
    DOTween.Kill(rt); DOTween.Kill(cg);            // KILL FIRST...
    Vector2 endPos = rt.anchoredPosition;          // ...THEN capture the settled position
    rt.anchoredPosition = endPos + Vector2.up * dist;
    cg.alpha = 0f;
    DOTween.To(() => cg.alpha, v => cg.alpha = v, 1f, dur).SetUpdate(true).SetTarget(cg);
    DOTween.To(() => rt.anchoredPosition, v => rt.anchoredPosition = v, endPos, dur)
           .SetEase(Ease.OutCubic).SetUpdate(true).SetTarget(rt);
}
```
If you capture `endPos` *before* killing, a fast re-open reads a mid-animation coordinate as the new
"settle" target and the panel drifts upward each time. Also `Kill` these tweens in the caller's
`OnDisable`/`OnDestroy`.

## Glass panel
`MakeGlassPanel` = translucent `GlassFill` Image + a 1px `GlassBorder` (Outline) + a thin top
`GlassHighlight` bar. There is **no blur** in stock uGUI. If you need readable text over a busy
background you'll add an opaque base layer — but that cancels most of the translucency, so decide
whether "glass" is worth it per panel rather than reflexively stacking both.

## Button scale feedback
A small `MonoBehaviour` implementing pointer enter/exit/down/up that `DOScale`s to hover (1.04) / press
(0.96) / 1.0. Strengthen color tint to ~0.30 Lerp (15% is imperceptible on dark UI) and fade ~0.12s.
**Reset `localScale = Vector3.one` in `OnDisable`** or a button disabled mid-hover stays at 1.04.
