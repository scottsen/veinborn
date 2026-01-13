# Veinborn Playtest Protocol

**Purpose:** Systematic validation of game fun factor and balance
**Duration:** 10-20 hours of gameplay across 3-5 sessions
**Status:** 🔴 NOT STARTED
**Critical:** This is the #1 blocker for launch readiness

---

## Why This Matters

**From GAPS_AND_NEXT_STEPS.md:**
> You have 858 passing tests, 19 monster types, 16 recipes, 14,534 lines of code, all 13 systems complete.
> **But you don't know if it's fun.**

**The gap isn't technical. The gap is validation.**

---

## The 8 Critical Questions

Play sessions must answer these questions with YES/NO + evidence:

| # | Question | Answer | Evidence/Notes |
|---|----------|--------|----------------|
| 1 | **Mining:** Is 3-5 turn vulnerability exciting or annoying? | ? | |
| 2 | **Ore Properties:** Do I care about hardness 78 vs 82? | ? | |
| 3 | **Crafting:** Is finding forges and crafting satisfying? | ? | |
| 4 | **Equipment:** Does gear make me feel powerful? | ? | |
| 5 | **Combat:** Is fighting tactical or button-mashing? | ? | |
| 6 | **Progression:** Do I want to go deeper? | ? | |
| 7 | **Death:** Do I immediately want to restart? | ? | |
| 8 | **Classes:** Do they feel meaningfully different? | ? | |

**Success threshold:** 6-8 YES → Game worth polishing
**Warning zone:** 3-5 YES → Needs design iteration
**Critical:** 0-2 YES → Fundamental issues

---

## Session Structure

### Session 1: Warrior Baseline (2-3 hours)
**Goal:** Experience core loop with simplest class

**Checklist:**
- [ ] Create new Warrior character
- [ ] Play until death or floor 5 (whichever first)
- [ ] Note every moment of confusion
- [ ] Note every moment of frustration
- [ ] Note every moment of excitement
- [ ] Complete findings template (see below)

**Focus questions:**
- How long until I understood what to do?
- When did combat feel good/bad?
- Was ore/crafting loop clear?
- Did I want to continue after first death?

### Session 2: Mage Validation (2-3 hours)
**Goal:** Test if classes feel different

**Checklist:**
- [ ] Create new Mage character
- [ ] Play until death or floor 5
- [ ] Compare to Warrior experience
- [ ] Note class-specific issues
- [ ] Complete findings template

**Focus questions:**
- Does Mage play differently than Warrior?
- Are class differences meaningful?
- Is starting equipment appropriate?
- Do stats affect gameplay noticeably?

### Session 3: Rogue Exploration (2-3 hours)
**Goal:** Validate 3rd class, deeper floors

**Checklist:**
- [ ] Create new Rogue character
- [ ] Attempt to reach floor 7+
- [ ] Test late-game balance
- [ ] Note difficulty curve
- [ ] Complete findings template

**Focus questions:**
- Does difficulty scale appropriately?
- Is late-game equipment powerful enough?
- Do deeper floors feel different?
- Is the "one more run" factor present?

### Session 4: Healer + Legacy System (2-3 hours)
**Goal:** Test 4th class and meta-progression

**Checklist:**
- [ ] Create new Healer character
- [ ] Test Legacy Vault functionality
- [ ] Use saved ore from previous runs
- [ ] Note meta-progression clarity
- [ ] Complete findings template

**Focus questions:**
- Is Healer viable solo?
- Is Legacy Vault system clear?
- Does saved ore feel meaningful?
- Is Pure vs Legacy prestige understandable?

### Session 5: Extended Marathon (3-6 hours)
**Goal:** Test replayability and "one more run" factor

**Checklist:**
- [ ] Pick favorite class
- [ ] Play multiple consecutive runs
- [ ] Attempt deepest floor possible
- [ ] Note when/if boredom sets in
- [ ] Complete findings template

**Focus questions:**
- How many runs before fatigue?
- Is there build variety?
- Do runs feel different?
- Would I play this without being the dev?

---

## Findings Capture Template

For EACH play session, capture:

### Session Metadata
- **Date:** YYYY-MM-DD
- **Duration:** X hours Y minutes
- **Character:** Class name
- **Final Floor:** Floor reached before death
- **Deaths:** Number of deaths this session

### Critical Moments

#### 😃 What Felt GOOD (Be specific)
```
Example: "Finding a mithril vein on floor 3 felt exciting because I knew I could craft a strong weapon"

1.
2.
3.
```

#### 😕 What Felt CONFUSING (Be specific)
```
Example: "I didn't know where forges were - spent 10 minutes wandering"

1.
2.
3.
```

#### 😠 What Felt FRUSTRATING (Be specific)
```
Example: "Mining got interrupted by monster, lost 4 turns worth of progress with no feedback"

1.
2.
3.
```

#### 🐛 Bugs Found
```
1.
2.
3.
```

### Balance Observations

#### Too Easy
```
Example: "Floor 2 goblins died in 1 hit with iron sword"

1.
2.
```

#### Too Hard
```
Example: "Floor 5 troll killed me in 2 hits, unavoidable"

1.
2.
```

#### Just Right
```
Example: "Floor 3 orc fight required tactical positioning"

1.
2.
```

### Specific Metrics

| Metric | Value | Feeling |
|--------|-------|---------|
| Time to first death | ___min | Too fast / About right / Too slow |
| Time to find forge | ___min | Too long / About right / Quick |
| Crafted items | ___ | Too few / About right / Too many |
| Ore veins mined | ___ | Too few / About right / Too many |
| Floors cleared | ___ | Expected less / About right / Expected more |

### The "Would I Play This?" Test

**Critical question:** If this game was released by someone else, would you:
- [ ] Play it for 10+ hours
- [ ] Play it for 2-3 hours
- [ ] Play it for 30 minutes
- [ ] Uninstall after 5 minutes

**Why?** (Be brutally honest)
```

```

---

## Analysis After All Sessions

Once all 5 sessions complete, analyze:

### Pattern Recognition
- What complaints repeated across sessions?
- What excitement repeated across sessions?
- Which class felt best? Why?
- Which floors felt best balanced?

### Priority Issues
Categorize all findings:

**🔥 CRITICAL (Must fix before any launch):**
1.
2.
3.

**⚠️ HIGH (Needed for good experience):**
1.
2.
3.

**📝 MEDIUM (Nice to have):**
1.
2.
3.

**💭 LOW (Future enhancement):**
1.
2.
3.

### Answer the 8 Questions
Go back to the table at top of this document and fill in:
- Answer (YES/NO)
- Evidence from sessions

**Final score: ___/8 YES answers**

---

## Next Actions Based on Score

### If 6-8 YES: Polish Sprint
**The game is fun! Now make it learnable and balanced.**

Priority order:
1. Fix game-breaking bugs (if any found)
2. Implement tutorial system (6-8 hours)
3. Fix top 3 UX issues (4-6 hours)
4. Balance tuning based on data (4-8 hours)
5. Get external playtesters

Timeline: 2 weeks to launch-ready state

### If 3-5 YES: Design Iteration
**Core loop works but needs refinement.**

Priority order:
1. Fix the NO answers (identify what's broken)
2. Iterate on specific systems (mining, crafting, combat)
3. Re-playtest after fixes
4. Then move to Polish Sprint

Timeline: 2-4 weeks before polish phase

### If 0-2 YES: Fundamental Issues
**The game needs major design changes.**

Actions:
1. Identify core problem (boring combat? tedious mining? no hook?)
2. Design alternative approaches
3. Prototype changes
4. Re-evaluate

Timeline: 4-6 weeks before re-assessment

---

## Playtest Execution Tips

### Before Each Session
- [ ] Clear terminal
- [ ] Have notebook + pen ready (paper is faster than typing)
- [ ] Set 2-3 hour timer (take breaks)
- [ ] Disable distractions (phone, email)
- [ ] Commit to honest notes (not what you wish, what you feel)

### During Play
- **Write down EVERY confusing moment immediately**
- Don't rationalize issues ("I'm sure players will figure it out")
- Note times (e.g., "10min in: still don't know what ore hardness means")
- Screenshot interesting moments if possible
- Play like a player, not a developer

### After Each Session
- **Fill out findings template while fresh** (memory fades in 30min)
- Rate the session 1-10 for "fun factor"
- Note if you want to play more RIGHT NOW (strong signal!)
- Save findings as: `playtest-findings-YYYYMMDD-CLASS.md`

---

## Success Criteria

This playtest phase is COMPLETE when:

- [ ] All 5 sessions completed (10-20 total hours)
- [ ] All 8 critical questions answered with evidence
- [ ] Findings captured for each session
- [ ] Pattern analysis completed
- [ ] Priority issues list created
- [ ] Next action plan determined based on score

**Estimated time commitment:** 15-25 hours (10-20 play + 5 analysis)

**Blocker status:** This is the #1 blocker. Everything else waits for this.

---

## Integration with Development

After playtest findings exist:

1. **Create issues** for each CRITICAL finding
2. **Prioritize** based on impact × frequency
3. **Fix** rapidly (target: 1-2 days per critical issue)
4. **Re-test** specific fixes (30min smoke tests)
5. **Iterate** until issues resolved

**Goal:** Findings → Fixes → Validation loop < 1 week

---

## Notes

- This protocol is not optional - it's the critical path
- Honest findings are more valuable than wishful thinking
- Paper notes during play, digital template after (faster workflow)
- If you find yourself making excuses for the game, write that down too
- The goal is truth, not validation of existing work

**Remember:** 858 tests passing doesn't matter if the game isn't fun.

---

**Last updated:** 2026-01-08
**Status:** Ready for execution
**Next:** Start Session 1 (Warrior Baseline)
