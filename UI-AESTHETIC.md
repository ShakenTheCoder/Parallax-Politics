# Parallax Politics — UI Aesthetic Guidelines

## Design Philosophy

Parallax Politics is a governmental-grade political intelligence platform. The visual language must convey:

- **Authority**: Uncompromising clarity and official gravitas
- **Security**: Handling of classified, decision-grade intelligence
- **Precision**: Data-driven outputs with absolute traceability
- **Sovereignty**: Philippine political context with global intelligence standards

The interface is designed for two primary user categories:
1. **Principals** (Governors, Senators, Government leaders) — Command View
2. **Strategists** (Campaign Managers, Analysts) — Intelligence View

---

## Color System

### Primary Palette

| Token | Light Mode | Dark Mode | Usage |
|-------|------------|-----------|-------|
| `--background` | `#ffffff` | `#000000` | Page background |
| `--foreground` | `#000000` | `#ffffff` | Primary text, borders |
| `--border` | `#000000` | `#ffffff` | Dividers, card borders |
| `--muted` | `#f5f5f5` | `#1a1a1a` | Secondary backgrounds |
| `--muted-foreground` | `#666666` | `#999999` | Secondary text |

### Semantic Colors

| Token | Hex | Usage |
|-------|-----|-------|
| Green | `#22c55e` | Success, ready states, opportunities, positive KPIs |
| Yellow | `#eab308` | Warning, building states, cautionary data |
| Red | `#ef4444` | Critical, failed states, risks, archive actions |

### Color Usage Rules

- **Borders**: Always 1px solid `var(--border)` for containers
- **Accent Borders**: 2px solid `var(--foreground)` for emphasis (action cards)
- **Status Indicators**: Color-coded borders with matching text
- **Semantic Backgrounds**: 5% opacity tints for risk/opportunity cards

---

## Typography

### Font Stack

```css
font-family: var(--font-inter), Arial, Helvetica, sans-serif;
```

- **Primary**: Inter (variable font, weights 400, 500, 600, 700)
- **Fallbacks**: Arial, Helvetica, system sans-serif
- **Monospace**: System monospace for data/code display

### Type Scale

| Element | Size | Weight | Letter Spacing | Usage |
|---------|------|--------|----------------|-------|
| Display | `2.25rem` (36px) | 700 | `tight` (-0.025em) | Page titles (h1) |
| Title | `1.5rem` (24px) | 700 | `tight` | Section headers |
| Subtitle | `1.125rem` (18px) | 600 | normal | Card titles |
| Body | `0.875rem` (14px) | 400 | normal | Primary content |
| Small | `0.75rem` (12px) | 400-600 | `widest` (0.1em) | Labels, metadata |
| Micro | `0.625rem` (10px) | 700 | `widest` (0.1em) | Status badges, tags |

### Typography Patterns

- **Section Titles**: `text-xs font-semibold tracking-widest uppercase text-muted-foreground`
- **Status Badges**: `text-[10px] font-bold tracking-widest uppercase`
- **Monospace Data**: `text-xs font-mono` for scores, dates, IDs
- **Labels**: UPPERCASE with wide tracking for all metadata labels

---

## Spacing & Layout

### Container System

| Container | Max Width | Padding |
|-----------|-----------|---------|
| Page | `100%` | `px-4` (1rem) |
| Content | `max-w-4xl` (896px) | `py-10` (2.5rem) |
| Card | `100%` | `p-4` to `p-6` |

### Spacing Scale

- **XS**: `0.25rem` (4px) — Icon gaps, inline spacing
- **SM**: `0.5rem` (8px) — Tight component spacing
- **MD**: `1rem` (16px) — Standard gaps
- **LG**: `1.5rem` (24px) — Section spacing
- **XL**: `2rem` (32px) — Major sections
- **2XL**: `2.5rem` (40px) — Page-level spacing

### Layout Principles

- **Single-column**: Most content flows vertically
- **Max-width**: Content constrained to `max-w-4xl` for readability
- **Borders**: Heavy use of 1px borders to define containers
- **Stacking**: Vertical rhythm with consistent `space-y` gaps

---

## Components

### Buttons

#### Primary Button
```
bg-foreground text-background font-medium px-4 py-3
hover:opacity-90 transition-opacity
disabled:opacity-50
```

#### Secondary Button
```
border border-border px-3 py-1.5 text-sm
hover:bg-border transition-colors
```

#### Danger Button
```
border border-red-500 text-red-500 px-3 py-1.5 text-xs
hover:bg-red-500 hover:text-background transition-colors
```

### Cards

#### Standard Card
```
border border-border p-4 space-y-2
```

#### Emphasis Card (Action Card)
```
border-2 border-foreground p-5 space-y-4
```

#### Status Cards
```
/* Risk */
border border-red-500/60 bg-red-500/5 p-5

/* Opportunity */
border border-green-500/60 bg-green-500/5 p-5

/* Warning */
border border-yellow-500/60 bg-yellow-500/5 p-5
```

### Inputs

```
px-4 py-3 border border-border bg-background text-foreground
placeholder:text-muted-foreground
focus:outline-none focus:ring-2 focus:ring-foreground
disabled:opacity-50
```

### Badges & Tags

#### Status Badge
```
text-[10px] border px-2 py-0.5 font-bold tracking-widest uppercase
/* ready */ border-green-500 text-green-500
/* building */ border-yellow-500 text-yellow-500
/* failed */ border-red-500 text-red-500
```

#### Tag
```
text-xs border border-border px-2 py-0.5 text-muted-foreground
```

---

## Navigation

### Navbar

```
border-b border-border bg-background/80 backdrop-blur sticky top-0 z-50
h-16 flex items-center justify-between
max-w-4xl mx-auto px-4
```

#### Brand
```
text-xl font-bold tracking-tight
```

#### Nav Links
```
text-sm font-medium transition-colors hover:text-foreground
/* active */ text-foreground font-semibold
/* inactive */ text-muted-foreground
```

---

## Visual Hierarchy

### Information Priority

1. **Critical Alerts**: Red-bordered cards, top of viewport
2. **Action Cards**: Double-border, 24-72h timeframe
3. **Identity Panel**: Collapsible, always available
4. **Brief Content**: Standard cards, chronological
5. **History**: Collapsible, bottom of page
6. **Metadata**: Small text, muted color, bottom of cards

### Dividers

- Primary: `border-b border-border` for major sections
- Secondary: `border-t border-border` within cards
- Accent: `border-l-2 border-foreground` for quoted content

---

## Accessibility

### Contrast

- All text maintains WCAG 4.5:1 contrast ratio minimum
- Borders provide visual structure without relying solely on color
- Status indicators use both color AND icon/text

### Focus States

```
focus:outline-none focus:ring-2 focus:ring-foreground
```

### Motion

- Transitions: `150ms` duration for hover states
- Progress bars: `700ms` for smooth fills
- Pulse: Only for running/pending indicators

---

## Dark Mode

System respects `prefers-color-scheme: dark` with inverted colors:
- Background/Foreground swap
- Muted tones adjust for dark surfaces
- Semantic colors (green/yellow/red) remain consistent

---

## File Locations

| Asset | Path |
|-------|------|
| Global Styles | `/src/app/globals.css` |
| Layout | `/src/app/layout.tsx` |
| Navbar | `/src/components/Navbar.tsx` |
| Font | Inter via next/font/google |
