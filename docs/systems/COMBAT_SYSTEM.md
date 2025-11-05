# Combat System Design

## Core Combat Loop

### 1. Initiative Phase
- Speed + Dexterity modifier
- Status effects modify order
- Equipment weight impacts speed

### 2. Action Phase
- Major Action: Attack, Cast, Use Item
- Minor Action: Move, Interact, Quick Item
- Reaction: Counter, Dodge, Shield Block
- Free Action: Talk, Drop Item

### 3. Resolution Phase
#### Attack Resolution
- Base Hit Chance = 50% + (Attacker Accuracy - Target Evasion)
- Critical Hit = Natural 20 or (Precision > Target's Defense)
- Damage = Base + Strength + Weapon + (Crit × Multiplier)

#### Defense Resolution
- Damage Reduction = Armor + Constitution + Buffs
- Block Chance = Shield + Skill + Stance
- Dodge Chance = Evasion + Speed - Equipment Load

### 4. Effect Phase
- Status Effect Applications
- Damage Over Time
- Healing Over Time
- Buff/Debuff Duration

## Combat Modifiers

### Positioning
```
- Flanking: +20% Critical Hit Chance
- High Ground: +2 to Attack Rolls
- Confined Space: -2 to Evasion
- In Water: -25% Movement Speed
- In Darkness: -4 to Attack Rolls
```

### Status Effects
```
- Bleeding: -1 HP per turn, -1 to all rolls
- Burning: 2 Fire damage per turn, chance to spread
- Frozen: -50% Speed, +4 Defense
- Poisoned: -2 HP per turn, -25% Healing
- Stunned: Skip next turn, -4 to Defense
```

### Combat Stances
```
Aggressive
- +2 Attack
- -2 Defense
- +25% damage
- -25% dodge chance

Defensive
- -1 Attack
- +3 Defense
- +50% block chance
- -25% damage

Balanced
- No modifiers
- +1 to all saving throws

Mobile
- +2 Movement
- +2 Evasion
- -1 Attack
- Can't block
```

## Special Combat Rules

### Chain Attacks
1. On Critical Hit, chance for bonus attack
2. Each chain reduces accuracy by 25%
3. Maximum 3 chains per turn
4. Each chain hits a new target within range

### Combo System
```
Build combo meter through:
- Successful attacks: +1
- Critical hits: +2
- Skill usage: +1
- Taking damage: -1
- Missing attacks: -2

Combo Levels:
1-3: No bonus
4-6: +1 damage
7-9: +2 damage, +10% crit
10+: +3 damage, +20% crit, special move available
```

### Weapon Techniques

#### Light Weapons
- Quick Strike: 2 attacks at -2 penalty
- Precision Strike: -25% damage, +50% crit chance
- Defensive Stance: Can use weapon to parry

#### Heavy Weapons
- Power Attack: -2 accuracy, +50% damage
- Cleave: Hit multiple adjacent targets
- Guard Crush: Reduce target's defense

#### Ranged Weapons
- Aimed Shot: Use action to gain +4 next attack
- Quick Shot: -2 penalty but doesn't end movement
- Cover Fire: Reduce enemy accuracy

## Environment Interaction

### Special Actions
```
Grappling:
1. Contest of Strength
2. Winner can:
   - Throw target (damage + prone)
   - Pin target (immobilize)
   - Disarm target (lose weapon)

Pushing:
1. Strength contest
2. Success moves target 5 feet
3. Additional effects if pushed into hazards

Disarming:
1. Attack vs Defense +4
2. Success drops target's weapon
3. Critical success lets you catch weapon
```

### Environmental Effects
```
- Breaking Objects: Strength check vs object durability
- Moving Through Enemies: Contest of Strength
- Jumping Gaps: Dexterity check vs distance
- Swimming: Constitution check each turn
- Climbing: Strength check each 10 feet
```

## Environmental Affinities

Combat choices in different environments build long-term mastery. Repeated exposure creates permanent benefits.

### Darkness Affinity
**Built by:** Fighting in dim/dark areas
**Unlocks:**
- Shadow sight (see further in darkness)
- Stealth bonuses (+10% → +30% over time)
- Critical damage from shadows
- Eventually: "Shadow Step" ability

### Water/Wetland Affinity
**Built by:** Combat in water, rain, swamps
**Unlocks:**
- Fluid movement (reduced water penalties)
- Resistance to water-based attacks
- Enhanced dodge in wet conditions
- Eventually: "Tidal Flow" combat style

### Fire Zone Affinity
**Built by:** Fighting near lava, flames, burning areas
**Unlocks:**
- Heat resistance (reduced fire damage)
- Fire weapon enhancement
- Aggression bonuses near flames
- Eventually: "Burning Resolve" stance

### Heights Affinity
**Built by:** Combat on elevated terrain, cliffs, stairs
**Unlocks:**
- Improved accuracy from high ground
- Fall damage resistance
- Jump attack bonuses
- Eventually: "Leaping Strike" ability

### Confined Space Affinity
**Built by:** Corridor fighting, tight quarters
**Unlocks:**
- Reduced evasion penalty in tight spaces
- Shield/blocking bonuses
- Crowd control resistance
- Eventually: "Narrow Victory" technique

**Design Note:** Environmental affinities make positioning meaningful *beyond* a single fight. Choosing to engage in darkness repeatedly shapes your character permanently, encouraging players to develop signature tactics.

## Key Design Principles

1. **Meaningful Decisions**: Every turn matters
2. **Clear Feedback**: Players understand cause and effect
3. **Tactical Depth**: Position and timing create advantages
4. **Character Expression**: Different builds feel distinct
5. **Risk vs Reward**: Aggressive play offers rewards but carries danger
6. **Compounding Choices**: Today's tactics shape tomorrow's strengths