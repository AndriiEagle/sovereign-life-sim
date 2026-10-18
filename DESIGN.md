---
name: "Sovereign Emberglass Island"
version: "1.0"
style_prompt_short: >
  A calm alpine strategy diorama in moss, ivory and brass, with live isometric buildings and clear native controls.
style_prompt_full: >
  Preserve the existing Emberglass visual language: petrol background #0D1C1A, moss panels #142923, ivory #F0F0DF, lime #D6E6A0 and warm gold #E6C58D. Use Georgia headings and Segoe UI/system body text. Place a coherent 3:2 alpine island behind actual Canvas buildings and readable label plates. Use a world/sidebar desktop grid, one-column mobile layout, stable semantic project buttons and visible gold keyboard focus. Keep animation subtle and disable it for reduced motion. Never paint fake controls, finances or readiness into the artwork.
colors:
  primary:
    - name: "Petrol"
      hex: "#0D1C1A"
      role: "App background"
    - name: "Pale lime"
      hex: "#D6E6A0"
      role: "Primary action and active focus"
    - name: "Warm brass"
      hex: "#E6C58D"
      role: "Selection and keyboard focus"
---

# Sovereign visual contract

## Design Principles

An inviting, calm strategy world for deciding what to build next. Preserve the existing Emberglass moss, ivory and warm brass palette, editorial serif headings and real Canvas/DOM controls. The requested 8–9/10 is an artistic target for human review, never a measured completion score.

The original alpine island painting is scenery. Every building, label, selection, progress value, resource and action comes from the existing synthetic simulation. Keep the financial, provider, sandbox and source-evidence boundaries visible and accurate.

## Components and States

- Dark petrol background, moss panels, ivory body text, pale lime primary actions, warm gold selection/focus. Gold identifies selection; lime identifies focus; teal identifies scenario cashflow; muted sage identifies queued nodes.
- Georgia headings, native Segoe UI/system body fonts. No remote fonts or visual framework dependencies. Clear heading, context and action hierarchy. Raw technical evidence remains accessible in expandable details.
- A coherent 3:2 isometric island with live overlays and readable dark label plates. Reuse frozen Emberglass projection/sprite code unchanged; active adapter owns scenery, grid and selection. Render at device pixel ratio up to 2 and convert pointer coordinates in logical units.
- Desktop: world and project grid beside resource/focus/workshop cards. Tablet: one world column and two panel columns. Mobile: one column, two project buttons per row, internally scrollable 720px map, full-size form inputs, no page-width overflow.
- Keep 16 initial projects, two-focus-slot rule, commands, economics, recovery, request IDs and save semantics. Keyboard activation must retain the project button's focus after refresh. Every map node also has a semantic DOM button.
- Real anchors, meaningful labels, visible keyboard focus, native forms, accessible details and a skip link. Reduced motion disables scrolling and transitions; no ambient animation is required.
- Image failure leaves native terrain, sprites and selection working. Art never controls gameplay. Do not import proprietary game sprites.

## Sources and Evidence

Existing `engine-isometric-ui/styles.css` and the inspected live app established the palette and serif direction. The generated image prompt and provenance are in `engine-isometric-ui/assets/visual/ART_DIRECTION.md`. Actual browser checks and their limits are recorded in `audit/visual-refinement-acceptance.json`.

## Typography

Display: Georgia, normal weight, 39–49px hero / 23–29px panel headings. Body: Segoe UI/system, 14px base, 11–12px explanatory text, 16px mobile form inputs. Small 8–10px labels carry secondary metadata, never the only accessible project selector.

## Spacing and Grid

Desktop: maximum 1740px, 342px sidebar, 30px world padding, 8–16px component gaps. Four project columns, three below 1120px, two below 600px. Preserve a clear heading, context and action hierarchy.

## Imagery and Icons

Original generated alpine PNG, unmodified, 1536 × 1024, fixed 3:2 placement. Owned live SVG node assets and frozen Emberglass projection remain active. Native geometric brand mark; no proprietary game art, remote fonts, or icon dependency. Hide overlapping map labels by selection priority; all nodes remain available in the semantic project grid. Video, slides and social output: N/A.

## Responsive Behavior

At 820px use one world column and a two-column panel grid. At 600px use one panel column and an internally scrollable 720px canvas, initially centered; state refresh must preserve the user's pan. The document itself must not overflow.

## Motion

Only 150ms button and 250ms progress transitions plus native smooth anchor scrolling. The existing reduced-motion media query disables transitions, animation and smooth scrolling. No continuous animation or new timer.

## Accessibility

Preserve native forms, details, labels, disabled states, skip link and gold focus outlines. Project selection retains its existing DOM button and keyboard focus. Canvas selection has an equivalent DOM project button. Dark label plates protect text from scenery; screenshots do not establish complete accessibility conformance.

## Runtime Mapping

`engine-isometric-ui/styles.css` implements tokens and responsive layout. `engine-isometric-ui/emberglass.mjs` owns the Canvas scene and stable project-button reconciliation. `engine-isometric-ui/assets/visual/ART_DIRECTION.md` retains the actual generation prompt and asset provenance.

Acceptance requires actual desktop/narrow-screen renders, no document overflow, loaded local image, keyboard focus retention, node selection, work/rest, forge/expense, persisted state, image-failure fallback, and unchanged source snapshots. Python isolation and live provider/product gaps remain separate from visual acceptance.

## Do and Don't

Do keep the original source snapshots exact, expose real state, preserve mechanics and record visual evidence. Don't bake a dashboard into an image, treat synthetic CHF as revenue, infer personal health, enable providers, or call a subjective design target a measured acceptance score.
