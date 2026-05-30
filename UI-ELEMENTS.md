# Parallax Politics — UI Elements Documentation

## Application Structure

### Page Hierarchy

```
/                    → Landing (Auth Gateway)
/login               → Principal Authentication
/brief               → Strategic Brief (Main Dashboard)
/superadmin/enter    → Superadmin Authentication
/superadmin          → Principal Management Console
```

---

## Global Elements

### Layout (`/src/app/layout.tsx`)

**Components Present on ALL Pages:**
- `SessionProvider` — Authentication context wrapper
- `Navbar` — Global navigation
- Font loading (Inter, variable weights)
- HTML lang="en" with antialiasing

**Structure:**
```
<html>
  <body class="min-h-full flex flex-col">
    <SessionProvider>
      <Navbar />
      {children}
    </SessionProvider>
  </body>
</html>
```

### Navbar (`/src/components/Navbar.tsx`)

**Fixed Position**: Top, sticky, z-50
**Height**: 64px (h-16)
**Background**: Blur backdrop with border-bottom

**Elements:**

| Element | Condition | Description |
|---------|-----------|-------------|
| Brand | Always | "Parallax Politics" — links to `/brief` (auth) or `/` (guest) |
| Brief Link | `user` exists | Nav item to `/brief` |
| User Info | `user` exists | "Display Name (Role)" — small muted text |
| Logout | `user` exists | Secondary button style |
| Sign In | No `user` | Primary button style → `/login` |

**Navigation Logic:**
```typescript
navItems = user ? [{ label: "Brief", href: "/brief" }] : [];
```

---

## Page: Landing (`/src/app/page.tsx`)

**Route**: `/`
**Access**: Public
**Purpose**: Authentication gateway for the closed program

### Layout
- Full viewport height centering
- Max-width container: `max-w-sm`

### Elements

| Element | Style | Function |
|---------|-------|----------|
| Title | `text-5xl font-bold tracking-tight` | "Parallax" |
| Subtitle | `text-sm text-muted-foreground` | "Philippine Political Intelligence · Closed Program" |
| Sign In Button | Primary button, full width | Redirects to `/login` |
| Superadmin Link | `text-xs text-muted-foreground` | Hidden path to `/superadmin/enter` |

---

## Page: Login (`/src/app/login/page.tsx`)

**Route**: `/login`
**Access**: Public
**Purpose**: Principal authentication

### Layout
- Full viewport centering
- Max-width: `max-w-md`

### Elements

| Element | Specs |
|---------|-------|
| Title | "Log In" — `text-3xl font-bold tracking-tight` |
| Subtitle | "Welcome back to Parallax Politics" |
| Username Input | Type: text, placeholder: "Username" |
| Password Input | Type: password, placeholder: "Password" |
| Error Message | `text-sm text-red-600` centered |
| Submit Button | Full width, "Enter" / "Entering..." states |

### States
- **Loading**: `disabled`, button shows "Entering..."
- **Error**: Red text below inputs
- **Success**: Redirect to `/brief`

---

## Page: Brief Dashboard (`/src/app/brief/page.tsx`)

**Route**: `/brief`
**Access**: Authenticated principals only
**Purpose**: Primary intelligence interface — Command View

### Layout Structure
```
Container (max-w-4xl mx-auto px-4 py-10 space-y-8)
├── Header
├── Identity Panel (collapsible)
├── Generator Panel
├── Brief Detail (or Empty State)
└── History Panel (collapsible)
```

### 1. Header Section

| Element | Content |
|---------|---------|
| Eyebrow | "Parallax Politics · Strategic Brief" — tracking-widest uppercase |
| Title | `identity.full_name` — `text-4xl font-bold tracking-tight` |
| Subtitle | `role_title · party` — muted text |

### 2. Identity Panel

**State**: Collapsible (default: closed)
**Trigger**: Button with expand/collapse (+/−)

**Header Info:**
- Label: "Identity"
- Name: Principal's full name
- Role: Title + party affiliation
- Status Badge: `ready` | `building` | `none` (color-coded)

**Expanded Content:**
| Section | Content |
|---------|---------|
| Basics | JSON dump of identity basics |
| Current Position | JSON dump |
| Policy Stances | Key-value list |
| Controversies | Cards with severity scoring |
| Coverage Gaps | Yellow warning tags |

### 3. Generator Panel

**Purpose**: Trigger new brief generation
**Process**: SGA → DCAA → DEMCAA → Brief Synthesis

**Elements:**

| Element | Description |
|---------|-------------|
| Title | "Brief Generator" — uppercase label |
| Description | Pipeline stages and timing estimate |
| Generate Button | Primary CTA, disabled if PIDAA not ready |

**Progress Display (when generating):**
- Progress bar with percentage
- Step grid (4 steps): SGA, DCAA, DEMCAA, Brief
- Each step shows: status icon, key, label
- Error display (budget exhausted / failed)

### 4. Brief Detail (Generated Brief Display)

**Layout**: `space-y-6` vertical stack

#### Top Risk Card
```
Border: red-500/60 | Background: red-500/5
Header: "Top Risk · {time_horizon}"
Severity: "severity {X}/100" — monospace
Title: Risk label (lg font-semibold)
Summary: Risk description
```

#### Top Opportunity Card
```
Border: green-500/60 | Background: green-500/5
Header: "Top Opportunity · {time_horizon}"
Magnitude: "magnitude {X}/100" — monospace
Title: Opportunity label
Summary: Opportunity description
```

#### Topic Recommendations

**Section Title**: "Topic Recommendations ({count})"

**Topic Row Structure:**
```
Border container
├── Row header
│   ├── Index: "#{n}" — monospace
│   ├── Topic name
│   └── Stance Badge: LEAD | ENGAGE | AVOID
├── Rationale text
└── Angle (if stance ≠ avoid)
    └── Left border accent, italic text
```

**Stance Badge Styles:**
- `lead`: Green border/text
- `engage`: Yellow border/text
- `avoid`: Red border/text

#### Action Card Block

**Style**: `border-2 border-foreground` (emphasis)
**Header**: "Your Next Move · 24–72h" + confidence score

**Content Grid:**
| Field | Label Style | Content |
|-------|-------------|---------|
| What | uppercase micro | Action description |
| Who | uppercase micro | Responsible party |
| Where | uppercase micro | Location/channel |
| When | uppercase micro | Timing |
| How | uppercase micro | Method/approach |
| Proof needed | uppercase micro | Evidence requirements |
| Avoid | uppercase micro | Things to avoid |
| Success KPIs | uppercase micro | Bullet list |

#### Sources Block

**Section Title**: "Sources ({count})"

**Source Card:**
```
Border container
├── Title/URL link (break-all for long URLs)
├── Credibility score: "{X}%" — monospace
├── Domain + Date
└── Used-for tags: small bordered pills
```

#### Reasoning Block

**Style**: `border-l-2 border-foreground pl-5`
**Title**: "Why this brief"
**Content**: Explanation paragraph

#### Footer Metadata

**Style**: `text-xs text-muted-foreground text-center`
**Content**: `Generated {date} · {model} · ${cost} · confidence {X}%`

### 5. History Panel

**State**: Collapsible (default: closed)
**Title**: "History" + "{count} briefs"

**Brief List Item:**
```
Button row (click to load)
├── Date (muted, small)
├── Confidence score (monospace)
├── Action title (truncated)
└── Risk · Opportunity summary (truncated)
```

**Active State**: `bg-border/20` background highlight

### Empty State

```
Border: border-dashed border-border
Content: "No briefs yet." + context message
```

---

## Page: Superadmin Entry (`/src/app/superadmin/enter/page.tsx`)

**Route**: `/superadmin/enter`
**Access**: Public (requires superadmin code)
**Purpose**: Admin authentication gateway

### Layout
- Full viewport centering
- Max-width: `max-w-sm`

### Elements

| Element | Content |
|---------|---------|
| Title | "Superadmin" — `text-3xl font-bold tracking-tight` |
| Subtitle | "Parallax · Philippines POC" — uppercase micro |
| Code Input | Type: password, placeholder: "Superadmin code" |
| Error Message | Red text, connection error handling |
| Enter Button | Full width primary button |

**Error States:**
- Invalid code (403)
- Authentication required (401)
- Network/connection error

---

## Page: Superadmin Console (`/src/app/superadmin/page.tsx`)

**Route**: `/superadmin`
**Access**: Superadmin token required
**Purpose**: Principal management and identity orchestration

### Layout Structure
```
Top Bar (sticky)
Container (max-w-4xl mx-auto px-4 py-10 space-y-12)
├── Create Principal Section
└── Principals List Section

Modals:
├── Credentials Modal (one-time display)
└── Identity Drawer (slide-in detail)
```

### Top Bar

**Style**: `border-b border-border`, sticky top, z-30
**Elements:**
- Brand: "Parallax" — bold
- Badge: "Superadmin" — bordered tag
- Context: "Philippines POC" — muted text
- Sign out link — right aligned

### Create Principal Section

**Section Title**: "Create New Principal" — uppercase

#### Search Form
```
Flex row
├── Input: "Full name (e.g. Sara Duterte)"
└── Button: "Search" / "Searching…"
```

#### Disambiguation Card (appears after search)

**Layout:**
```
Border container, space-y-4
├── Header row
│   ├── Name + aliases
│   └── Photo (if available)
├── Info grid (2-col)
│   ├── Role, Party, Region, Born
├── Bio (italic, muted)
├── Source links (tag pills)
├── Ambiguity notes (yellow warning, if any)
├── Confidence score
└── Action row
    ├── "Confirm — this is the principal" (primary)
    └── [Hint input] + [Retry] (secondary)
```

### Principals List Section

**Section Title**: "Principals ({count})" — uppercase

#### Principal Row

```
Border container, flex row
├── Left: Info block
│   ├── Full name (font-medium)
│   └── Role · Party · @username (muted, small)
└── Right: Actions (shrink-0)
    ├── Status Badge (ready/building/failed)
    ├── Built date (hidden on mobile)
    ├── View button (secondary)
    ├── Rerun PIDAA button (secondary)
    └── Archive button (danger)
```

### Credentials Modal

**Trigger**: After successful principal creation
**Purpose**: Display one-time credentials

**Layout:**
```
Fixed overlay: bg-black/60, z-50
Modal: bg-background, border, max-w-sm
├── Title: "Credentials — shown once"
├── Warning: "Save these now..."
├── Display block: monospace, bordered
│   ├── Username: {value}
│   └── Password: {value}
└── Actions
    ├── Copy button (secondary)
    └── "I've saved these" (primary)
```

### Identity Drawer

**Trigger**: Click "View" on principal row
**Animation**: Slide-in from right
**Width**: `max-w-2xl`

**Header:**
- Name (bold, large)
- Role · Party (muted)
- Close button (✕)

**Content Sections:**
| Section | Data |
|---------|------|
| Status | Badge + built date + username |
| Coverage Gaps | Yellow warning tags (if any) |
| Basics | JSON block |
| Family | JSON block |
| Education | JSON block |
| Career Timeline | JSON block |
| Current Position | JSON block |
| Party History | JSON block |
| Electoral Record | JSON block |
| Policy Stances | JSON block |
| Voice Signature | JSON block |
| Controversies | JSON block |
| Network | JSON block |

---

## Shared Component Patterns

### Section Title Pattern

Used across all pages for subsection headers:
```typescript
function SectionTitle({ title }: { title: string }) {
  return (
    <p className="text-xs font-semibold tracking-widest uppercase text-muted-foreground">
      {title}
    </p>
  );
}
```

### Status Badge Pattern

```typescript
function StatusBadge({ status }: { status: string }) {
  const color =
    status === "ready" ? "text-green-500 border-green-500" :
    status === "building" ? "text-yellow-500 border-yellow-500" :
    status === "failed" ? "text-red-500 border-red-500" :
    "text-muted-foreground border-border";
  return <span className={`text-xs border px-2 py-0.5 ${color}`}>{status}</span>;
}
```

### Collapsible Panel Pattern

Used in Identity Panel and History Panel:
```typescript
const [open, setOpen] = useState(false);

<button onClick={() => setOpen(!open)}>
  {/* Header content */}
  <span>{open ? "−" : "+"}</span>
</button>
{open && <div>{/* Expanded content */}</div>}
```

---

## Responsive Behavior

### Breakpoints

| Breakpoint | Behavior |
|------------|----------|
| Default (<640px) | Single column, full width |
| `sm` (≥640px) | Show additional metadata |
| `md` (≥768px) | 2-column grids for risk/opportunity |
| `lg` (≥1024px) | Max-width containers active |

### Mobile Adaptations

- **Navbar**: User role hidden, compact spacing
- **Risk/Opportunity**: Stack vertically
- **Action Card Grid**: Single column on mobile
- **Generator Steps**: 2-column grid (sm) → 4-column (md+)
- **Superadmin List**: Actions wrap, date hidden

---

## State Management UI

### Loading States

| Context | Visual |
|---------|--------|
| Page load | "Loading…" muted text, centered |
| Button action | `disabled` + opacity-50 + loading text |
| Generation | Progress bar + step indicators |
| Polling | Step pulse animation |

### Error States

| Context | Visual |
|---------|--------|
| Form error | Red text below input |
| API error | Red text in panel |
| Connection | Specific messaging for network errors |

### Empty States

| Context | Message |
|---------|---------|
| No briefs | "No briefs yet." + context |
| No principals | "No principals yet." |
| No sources | Section hidden |

---

## File Reference

| Component | Path |
|-----------|------|
| Layout | `/src/app/layout.tsx` |
| Navbar | `/src/components/Navbar.tsx` |
| Landing | `/src/app/page.tsx` |
| Login | `/src/app/login/page.tsx` |
| Brief | `/src/app/brief/page.tsx` |
| Superadmin Entry | `/src/app/superadmin/enter/page.tsx` |
| Superadmin Console | `/src/app/superadmin/page.tsx` |
| Session Context | `/src/lib/SessionContext.tsx` |
| API Client | `/src/lib/api.ts` |
