# Beth Integration Plan for Brogue Documentation

**Date:** 2025-10-24
**Status:** Action Required
**Priority:** High

---

## Executive Summary

**Problem:** Brogue project documentation is NOT indexed in TIA's semantic search system (Beth), making it undiscoverable via `tia semantic search` and poorly presented via `tia beth explore`.

**Impact:**
- New developers can't find Brogue docs via semantic search
- `tia beth explore brogue` shows old session logs instead of architecture docs
- New critical docs (OPERATIONAL_EXCELLENCE_GUIDELINES.md, EVENTS_ASYNC_OBSERVABILITY_GUIDE.md) are invisible to Beth
- Knowledge graph relationships don't exist for Brogue

**Solution:** Add Brogue docs to semantic collections with proper weights and relationships.

---

## Current State Analysis

### What Beth Currently Shows

```bash
$ tia beth explore brogue
```

**Top Results:**
1. ⭐ 23.5 - `/sessions/divine-anvil-1021/README.md` (2 days old session)
2. ⭐ 21.0 - `/sessions/explosive-beam-1021/README.md` (2 days old session)
3. ⭐ 18.9 - `/sessions/icy-temple-1021/README.md` (2 days old session)
4. ⭐ 18.1 - `/projects/brogue/docs/future-multiplayer/BROGUE_PROXY_ROUTING.md` (Phase 2)

**Missing from top results:**
- ❌ `docs/architecture/OPERATIONAL_EXCELLENCE_GUIDELINES.md` (created today)
- ❌ `docs/architecture/EVENTS_ASYNC_OBSERVABILITY_GUIDE.md` (created today)
- ❌ `docs/architecture/MVP_DEVELOPMENT_GUIDELINES.md` (essential MVP doc)
- ❌ `docs/architecture/MVP_TESTING_GUIDE.md` (essential MVP doc)
- ❌ `docs/architecture/00_ARCHITECTURE_OVERVIEW.md` (START HERE doc)
- ❌ `docs/architecture/README.md` (navigation hub)

### Semantic Search State

```bash
$ tia semantic search "Brogue MVP operational excellence" --limit 5
```

**Result:** ZERO Brogue docs returned. Only TIA infrastructure docs.

**Collections that exist:**
- ✅ `tia-commands-code` (519 docs)
- ✅ `tia-docs-ai` (99 docs)
- ✅ `tia-docs-architecture` (62 docs - TIA architecture, not Brogue)
- ✅ `tia-docs-core` (62 docs)
- ✅ `tia-docs-guides` (92 docs)
- ✅ `tia-docs-infrastructure` (42 docs)
- ✅ `tia-docs-reference` (24 docs)
- ❌ **NO collection for project docs** (`/projects/brogue/docs/`)

---

## Recommended Solution

### Option 1: Create Project Docs Collection (Recommended)

**Create new collection:** `tia-projects`

**Rationale:**
- Brogue is first of many potential projects
- Clean separation between TIA system docs and project docs
- Allows project-specific weighting and relationships
- Scalable for future projects (NetHack, other games)

**Configuration:**

```yaml
# config/semantic_collections.yaml (or wherever collections are configured)

collections:
  tia-projects:
    name: "TIA Projects Documentation"
    description: "Documentation for projects built with TIA (Brogue, etc.)"
    paths:
      - "/home/scottsen/src/tia/projects/*/docs/**/*.md"
      - "/home/scottsen/src/tia/projects/*/README.md"
    exclude:
      - "**/.git/**"
      - "**/node_modules/**"
      - "**/Archive/**"
      - "**/future-multiplayer/**"  # Index separately if needed
    chunk_size: 1000
    chunk_overlap: 200
    priority_weight: 1.2  # Slightly higher than default for project docs
```

**Expected documents indexed:**
- `projects/brogue/docs/architecture/*.md` (~15 docs)
- `projects/brogue/docs/*.md` (MVP_ROADMAP, START_HERE, etc.)
- `projects/brogue/README.md`
- Future: `projects/nethack/docs/**/*.md` (when created)

**Total estimated:** ~25-30 Brogue docs

### Option 2: Add to Existing Collection (Alternative)

**Add Brogue to:** `tia-docs-architecture`

**Rationale:**
- Quick solution
- Brogue docs are architecture-focused
- No new collection needed

**Configuration:**

```yaml
collections:
  tia-docs-architecture:
    paths:
      - "/home/scottsen/src/tia/docs/architecture/**/*.md"
      - "/home/scottsen/src/tia/projects/brogue/docs/architecture/**/*.md"  # ADD THIS
```

**Downside:** Mixes TIA system architecture with Brogue project architecture.

---

## Document Weighting Strategy

### Priority Tiers for Brogue Docs

**Tier 1: Essential MVP Docs (Weight: 1.5)**
- `00_ARCHITECTURE_OVERVIEW.md` - START HERE doc
- `MVP_DEVELOPMENT_GUIDELINES.md` - Code style essentials
- `MVP_TESTING_GUIDE.md` - Testing essentials
- `OPERATIONAL_EXCELLENCE_GUIDELINES.md` - Best practices
- `EVENTS_ASYNC_OBSERVABILITY_GUIDE.md` - Critical before coding
- `README.md` (architecture) - Navigation hub

**Tier 2: Implementation Guides (Weight: 1.2)**
- `BASE_CLASS_ARCHITECTURE.md` - Design patterns
- `CONTENT_SYSTEM.md` - YAML content
- `MVP_ROADMAP.md` - What to build
- `START_HERE.md` - Project overview

**Tier 3: Reference Docs (Weight: 1.0)**
- `DECISIONS.md` - ADRs
- `LUA_INTEGRATION_STRATEGY.md` - Future planning
- Game design docs

**Tier 4: Phase 2/Future (Weight: 0.8)**
- `future-multiplayer/*.md` - Don't prioritize for MVP search

### Metadata Tags for Brogue Docs

```yaml
# Suggested metadata for each doc

OPERATIONAL_EXCELLENCE_GUIDELINES.md:
  tags:
    - brogue
    - mvp
    - essential
    - coding-standards
    - best-practices
  phase: mvp
  priority: tier-1
  read_before: coding

EVENTS_ASYNC_OBSERVABILITY_GUIDE.md:
  tags:
    - brogue
    - mvp
    - essential
    - async
    - events
    - textual
  phase: mvp
  priority: tier-1
  read_before: coding

MVP_DEVELOPMENT_GUIDELINES.md:
  tags:
    - brogue
    - mvp
    - essential
    - code-style
    - testing
  phase: mvp
  priority: tier-1
```

---

## Relationship Graph

### Document Relationships with Weights

```yaml
# Suggested relationship weights (higher = stronger connection)

relationships:
  # Core MVP reading path
  - source: "START_HERE.md"
    target: "00_ARCHITECTURE_OVERVIEW.md"
    weight: 1.0
    relationship: "read-next"

  - source: "00_ARCHITECTURE_OVERVIEW.md"
    target: "MVP_DEVELOPMENT_GUIDELINES.md"
    weight: 1.0
    relationship: "read-next"

  - source: "MVP_DEVELOPMENT_GUIDELINES.md"
    target: "MVP_TESTING_GUIDE.md"
    weight: 1.0
    relationship: "read-next"

  - source: "MVP_TESTING_GUIDE.md"
    target: "OPERATIONAL_EXCELLENCE_GUIDELINES.md"
    weight: 1.0
    relationship: "read-next"

  - source: "OPERATIONAL_EXCELLENCE_GUIDELINES.md"
    target: "EVENTS_ASYNC_OBSERVABILITY_GUIDE.md"
    weight: 1.0
    relationship: "read-next"

  # Complementary relationships
  - source: "OPERATIONAL_EXCELLENCE_GUIDELINES.md"
    target: "BASE_CLASS_ARCHITECTURE.md"
    weight: 0.7
    relationship: "complements"

  - source: "EVENTS_ASYNC_OBSERVABILITY_GUIDE.md"
    target: "BASE_CLASS_ARCHITECTURE.md"
    weight: 0.8
    relationship: "complements"
    context: "BASE_CLASS has EventBus design, EVENTS_ASYNC has MVP patterns"

  - source: "MVP_DEVELOPMENT_GUIDELINES.md"
    target: "CONTENT_SYSTEM.md"
    weight: 0.6
    relationship: "references"

  # Implementation relationships
  - source: "00_ARCHITECTURE_OVERVIEW.md"
    target: "MVP_ROADMAP.md"
    weight: 0.8
    relationship: "implementation-guide"

  - source: "MVP_ROADMAP.md"
    target: "MVP_CURRENT_FOCUS.md"
    weight: 0.9
    relationship: "current-work"
```

---

## Expected Beth Presentation After Integration

### Ideal `tia beth explore brogue` Output

```
🔍 EXPLORING: brogue (50 docs analyzed)
============================================================
🎯 STRONGEST HITS:
   ⭐ 25.0  [today]  .../brogue/docs/architecture/README.md
                     📌 NAVIGATION HUB - Start here for all Brogue docs

   ⭐ 24.5  [today]  .../brogue/docs/START_HERE.md
                     📌 PROJECT OVERVIEW - New developer onboarding

   ⭐ 24.0  [today]  .../brogue/docs/architecture/00_ARCHITECTURE_OVERVIEW.md
                     📌 MVP ARCHITECTURE - How the system works

   ⭐ 23.5  [today]  .../brogue/docs/architecture/MVP_DEVELOPMENT_GUIDELINES.md
                     📌 CODE STYLE - Essential standards

   ⭐ 23.0  [today]  .../brogue/docs/architecture/OPERATIONAL_EXCELLENCE_GUIDELINES.md
                     📌 BEST PRACTICES - Small methods, logging, errors

🔗 RELATED TOPICS (from strongest docs):
   🔥 mvp-coding → tia beth explore "mvp-coding"
   🔥 async-patterns → tia beth explore "async-patterns"
   🔥 event-driven → tia beth explore "event-driven"

📚 READING PATHS:
   1️⃣ New Developer: START_HERE.md → 00_ARCHITECTURE → MVP_DEVELOPMENT
   2️⃣ Before Coding: OPERATIONAL_EXCELLENCE → EVENTS_ASYNC_OBSERVABILITY
   3️⃣ Implementation: MVP_ROADMAP → BASE_CLASS_ARCHITECTURE

🌐 KNOWLEDGE CLUSTERS:
   📘 mvp-essential → 6 docs (tier-1 priority)
   📘 architecture → 8 docs
   📘 phase-2-future → 12 docs (lower priority)
```

### Ideal Semantic Search Results

```bash
$ tia semantic search "Brogue how to write good code" --limit 5
```

**Expected:**
1. ⭐⭐⭐⭐ `OPERATIONAL_EXCELLENCE_GUIDELINES.md` (0.92 - small methods, SRP)
2. ⭐⭐⭐⭐ `MVP_DEVELOPMENT_GUIDELINES.md` (0.89 - code style, PEP 8)
3. ⭐⭐⭐ `BASE_CLASS_ARCHITECTURE.md` (0.82 - clean patterns)
4. ⭐⭐⭐ `MVP_TESTING_GUIDE.md` (0.78 - TDD, testing)
5. ⭐⭐ `00_ARCHITECTURE_OVERVIEW.md` (0.74 - development workflow)

---

## Implementation Steps

### Step 1: Create Collection Configuration

```bash
# Create or update semantic collection config
vim ~/.tia/config/semantic_collections.yaml

# Add tia-projects collection (see Option 1 above)
```

### Step 2: Index Brogue Docs

```bash
# Scan for Brogue docs
tia semantic refresh scan tia-projects

# Update collection
tia semantic update tia-projects

# Verify indexing
tia semantic list
# Should show: tia-projects: ~30 docs, XXX chunks, XXX embeddings
```

### Step 3: Add Document Metadata

```bash
# For each Brogue doc, add frontmatter:
# ---
# tags: [brogue, mvp, essential]
# phase: mvp
# priority: tier-1
# read_before: coding
# ---
```

### Step 4: Configure Relationships

```bash
# If Beth supports relationship configuration:
# Add relationships.yaml or similar

# If not, relationships may be inferred from:
# - Cross-references in docs
# - Frontmatter "related_docs" fields
# - Reading order in README.md
```

### Step 5: Test and Validate

```bash
# Test semantic search
tia semantic search "Brogue MVP coding best practices" --limit 5
# Should return OPERATIONAL_EXCELLENCE_GUIDELINES.md as #1

# Test Beth explore
tia beth explore brogue
# Should show architecture docs, not session logs

# Test specific queries
tia semantic search "Brogue async await Textual" --limit 3
# Should return EVENTS_ASYNC_OBSERVABILITY_GUIDE.md

tia semantic search "Brogue small methods single responsibility"
# Should return OPERATIONAL_EXCELLENCE_GUIDELINES.md
```

---

## Success Criteria

### After Integration

**✅ Semantic Search:**
- [ ] `tia semantic search "Brogue"` returns project docs (not TIA system docs)
- [ ] Essential MVP docs rank in top 5 for relevant queries
- [ ] OPERATIONAL_EXCELLENCE_GUIDELINES.md findable via "best practices" query
- [ ] EVENTS_ASYNC_OBSERVABILITY_GUIDE.md findable via "async" or "events" query

**✅ Beth Explore:**
- [ ] `tia beth explore brogue` shows architecture docs first
- [ ] Session READMEs rank below architecture docs
- [ ] Related topics include "mvp", "async", "testing"
- [ ] Reading paths suggested

**✅ Document Discoverability:**
- [ ] New developer can find START_HERE.md
- [ ] Developer looking for coding standards finds MVP_DEVELOPMENT_GUIDELINES.md
- [ ] Developer about to code finds EVENTS_ASYNC_OBSERVABILITY_GUIDE.md
- [ ] Searches for "logging" surface OPERATIONAL_EXCELLENCE_GUIDELINES.md

---

## Alternative: Quick Fix Without Semantic Index

**If semantic indexing is complex, at minimum:**

### Update Beth Topic Weights Manually

```bash
# If Beth has a topics configuration:
# ~/.tia/beth/topics.yaml

topics:
  brogue:
    priority_docs:
      - path: "projects/brogue/docs/architecture/README.md"
        weight: 2.0

      - path: "projects/brogue/docs/architecture/OPERATIONAL_EXCELLENCE_GUIDELINES.md"
        weight: 1.8

      - path: "projects/brogue/docs/architecture/EVENTS_ASYNC_OBSERVABILITY_GUIDE.md"
        weight: 1.8

      - path: "projects/brogue/docs/architecture/MVP_DEVELOPMENT_GUIDELINES.md"
        weight: 1.6

      - path: "projects/brogue/docs/architecture/00_ARCHITECTURE_OVERVIEW.md"
        weight: 1.6

    downweight_patterns:
      - pattern: "sessions/*/README.md"
        weight: 0.3  # De-prioritize session logs

      - pattern: "future-multiplayer/**"
        weight: 0.5  # De-prioritize Phase 2 docs
```

---

## Maintenance Plan

### Regular Updates

**Weekly:**
- [ ] Run `tia semantic refresh scan tia-projects` to detect new docs
- [ ] Update collection after adding new Brogue docs

**Monthly:**
- [ ] Review Beth explore results for "brogue" query
- [ ] Adjust weights if wrong docs surfacing
- [ ] Update relationships as doc structure evolves

**After Major Doc Changes:**
- [ ] Re-index collection: `tia semantic update tia-projects`
- [ ] Test top queries
- [ ] Update relationship graph if reading order changed

---

## Questions for TIA Team

1. **Collection Configuration:** Where is the semantic collection config file?
2. **Document Metadata:** Does TIA semantic support frontmatter tags?
3. **Relationships:** How are document relationships configured?
4. **Weighting:** Can we set custom weights per document or pattern?
5. **Auto-refresh:** Should we enable `tia semantic refresh start` for automatic updates?

---

## Next Actions

**Immediate (Today):**
1. ✅ Create this plan document
2. ⬜ Locate semantic collection configuration
3. ⬜ Add Brogue docs to semantic index (Option 1 or 2)
4. ⬜ Test semantic search for Brogue docs

**Short-term (This Week):**
1. ⬜ Configure document weights/priorities
2. ⬜ Set up relationships between docs
3. ⬜ Validate Beth presentation
4. ⬜ Document for team how to maintain

**Long-term:**
1. ⬜ Enable auto-refresh for project docs
2. ⬜ Monitor search effectiveness
3. ⬜ Adjust weights based on usage patterns

---

**Status:** Ready for implementation
**Owner:** TBD
**Timeline:** 1-2 hours for initial setup

---

## References

- Beth topic indexing: `tia beth --help`
- Semantic search: `tia semantic --help`
- Collection management: `tia semantic list`, `tia semantic health`
- This plan: `/projects/brogue/docs/BETH_INTEGRATION_PLAN.md`
