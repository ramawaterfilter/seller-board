# web/ — UI rules (nested)
- Visual parity profile through design tokens only; no raw colour literals outside web/src/design/; Lucide icons only; no vendor name, logo, CSS, copy or screenshots.
- Money renders only through <Money> from 4-dp API strings; no client-side money arithmetic; times through <When value tz>.
- Omitted marketing screens (SCR-040/041/043..046/074/075/133/134) have no route, nav entry or component.
- Mobile-first: 390x844 journeys, touch targets >= 44 px, WCAG 2.1 AA in both themes; the service worker never caches /api/ money responses.
## Code Review Rules
- P0: client-side money arithmetic or float formatting of amounts, PII or tokens in localStorage/IndexedDB, a route for an omitted screen.
- P1: missing axe check, a raw colour literal, a status shown by colour only.
