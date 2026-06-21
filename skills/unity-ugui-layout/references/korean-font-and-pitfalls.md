# Korean / CJK font pipeline & common pitfalls

The single most common silent failure in code-built Unity UI: **CJK (Korean/Japanese/Chinese) text
renders as tofu (□)**. This file is the complete fix. It generalizes to any non-Latin script.

## Why it breaks

1. **Runtime-built text has no font.** A `UITheme.UIFont` static that is assigned only by *editor*
   builder scripts (`AssetDatabase.LoadAssetAtPath`) is **null at play time** — statics reset on domain
   reload, and editor APIs don't run in a build. Any UI created at runtime (`MonoBehaviour` dialogs,
   minigames, popups) then falls through to TMP's default Latin font (LiberationSans) → every CJK glyph
   is □. Editor-built text looks fine (font baked into the serialized component) which masks the bug
   until you hit a runtime-built screen.
2. **Execution order.** Even with a binder, if a view builds its UI in `Awake` it may run *before* the
   binder assigns the font. Build runtime UI in `Start` (or guard lazily), and make the binder
   `[DefaultExecutionOrder(-1000)]` so its `Awake` wins.
3. **Missing glyphs.** A CJK font may lack punctuation like em-dash `—`, arrows, or symbols → those
   specific chars tofu even when Hangul renders. Solved by a fallback font.

## The fix (three layers, defense in depth)

### Layer 1 — runtime font binder (MonoBehaviour)
```csharp
[DefaultExecutionOrder(-1000)] // run before any UI Awake
public class UIThemeFontBinder : MonoBehaviour {
    [SerializeField] TMP_FontAsset koreanFont; // assign in inspector / wire from a builder
    void Awake() {
        if (koreanFont != null) UITheme.UIFont = koreanFont;
    }
}
```
Place one in the scene; wire `koreanFont` to your CJK SDF asset. A serialized reference (not a hardcoded
path, not `Resources.Load` from `[RuntimeInitializeOnLoadMethod]` which can't load project assets)
makes the font swappable and survives builds.

### Layer 2 — ResolveFont fallback in UITheme
```csharp
public static TMP_FontAsset UIFont; // injected by binder at runtime, by builders in editor
static TMP_FontAsset ResolveFont() => UIFont != null ? UIFont : TMP_Settings.defaultFontAsset;
public static void ApplyFont(TMP_Text t) {
    if (t == null) return;
    var f = ResolveFont();
    if (f != null) t.font = f;
}
```
Every `MakeText`/label helper calls `ApplyFont`, so even with no binder present the text gets *a*
CJK-capable font as long as the TMP default is set (Layer 3).

### Layer 3 — TMP default font + fallback (project-wide safety net)
Set your CJK SDF as **`TMP_Settings.defaultFontAsset`** so *all* TMP text uses it by default, and add a
broad-coverage CJK font (e.g. NotoSansKR SDF) to that asset's **fallback font table** so any glyph the
primary font lacks (like `—`) is rendered by the fallback instead of tofu.

## Creating a CJK TMP font asset from a .ttf (Dynamic SDF)

CJK fonts have 11k+ glyphs — a static pre-baked atlas would be enormous. Use **Dynamic** atlas mode so
glyphs rasterize on demand at runtime. Programmatic creation (editor):

```csharp
Font src = AssetDatabase.LoadAssetAtPath<Font>("Assets/.../MyFont.ttf");
var fa = TMP_FontAsset.CreateFontAsset(
    src, 90, 9, GlyphRenderMode.SDFAA, 1024, 1024,
    AtlasPopulationMode.Dynamic, enableMultiAtlasSupport: true);
fa.name = "MyFont SDF";
AssetDatabase.CreateAsset(fa, "Assets/.../MyFont SDF.asset");
// persist atlas texture + material as SUB-ASSETS or they vanish on reimport:
if (fa.atlasTextures?.Length > 0) {
    fa.atlasTextures[0].name = "MyFont SDF Atlas";
    AssetDatabase.AddObjectToAsset(fa.atlasTextures[0], fa);
}
if (fa.material != null) {
    fa.material.name = "MyFont SDF Material";
    AssetDatabase.AddObjectToAsset(fa.material, fa);
}
EditorUtility.SetDirty(fa);
AssetDatabase.SaveAssets();
AssetDatabase.ImportAsset("Assets/.../MyFont SDF.asset");
```
Setting it as TMP default via code:
```csharp
var settings = Resources.Load<TMP_Settings>("TMP Settings");
var so = new SerializedObject(settings);
so.FindProperty("m_defaultFontAsset").objectReferenceValue = fa;
so.ApplyModifiedPropertiesWithoutUndo();
EditorUtility.SetDirty(settings);
```
Adding a fallback:
```csharp
fa.fallbackFontAssetTable ??= new List<TMP_FontAsset>();
if (!fa.fallbackFontAssetTable.Contains(noto)) fa.fallbackFontAssetTable.Add(noto);
EditorUtility.SetDirty(fa);
```
`AtlasPopulationMode` enum: **Static = 0, Dynamic = 1** (in the .asset YAML, `m_AtlasPopulationMode: 1`
means Dynamic — don't misread it as Static).

## Verifying it actually works
- Play-mode `ScreenCapture` is often white for runtime-router HUDs; editor-mode game-view capture of
  in-world signage is a more reliable visual check.
- Watch the console for `"The character with Unicode value \uXXXX was not found in font asset ... replaced by □"`
  — that warning is your tofu detector. Zero of those = success.
- A font with a Dynamic atlas + `m_ClearDynamicDataOnBuild: 1` rasterizes glyphs at runtime, so the
  *first* time a new glyph appears in a real build there can be a one-frame hitch. Usually invisible;
  pre-warm critical strings if it matters.

## Licensing (don't skip)
A `.ttf` embedded in a build (`includeFontData: 1`) is redistribution. Confirm the font's license
permits embedding + commercial distribution, and keep the license file in the repo (as Noto fonts do
with their OFL.txt). Flag this to the user — it's a real shipping blocker, not a nicety.

## Other code-UI pitfalls (non-font)
- **DOTween UI-module shortcuts unavailable:** `DOFillAmount`, `Graphic.DOColor`, `CanvasGroup.DOFade`,
  `RectTransform.DOAnchorPos` live in DOTween's UI module which may not be referenced by a game asmdef.
  Symptom: CS1061/CS1929 compile errors. Fix: use core `DOTween.To(() => x, v => x = v, target, dur)`.
- **`execute_code`/codegen with BOM:** some MCP code-exec paths prepend a BOM that breaks C# compile;
  prefer editor-script + menu execution, or direct asset/YAML edits via the Unity asset tools.
- **"Wired" ≠ "renders":** a SerializeField populated by a builder can still be invisible (wrong Image
  type, zero size, behind another panel). Confirm in actual play, not just by checking the reference.
- **Builder idempotency:** editor builders that re-create children must clear or find-or-create existing
  ones, or re-running the menu stacks duplicate headers/buttons.
