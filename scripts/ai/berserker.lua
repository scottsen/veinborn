--[[
Berserker AI Behavior

Characteristics:
- Aggressive when healthy (>70% HP)
- Enraged when damaged (<70% HP):
  * Increased chase range
  * Never flees
  * Higher aggression
- Suitable for: Orcs, Barbarians, Berserkers

Configuration (in ai_behaviors.yaml):
  berserker:
    description: "Aggressive fighter, enraged when wounded"
    chase_range: 8
    enraged_chase_range: 15
    enrage_threshold: 0.7  # Enrage when HP < 70%
    attack_on_sight: true

Usage:
  Monster with ai_type="berserker" will use this behavior.
  The update() function is called each turn for AI decision-making.
--]]

-- Behavior update function
-- Called each turn for monsters with ai_type="berserker"
-- @param monster: Monster entity table
-- @param config: Behavior configuration from YAML
-- @return: Action descriptor {action = "...", target_id = "..." (optional)}
function update(monster, config)
    -- Get player (primary target)
    local player = veinborn.get_player()

    if not player or not player.is_alive then
        -- No target - wander
        return {action = "wander"}
    end

    -- Calculate HP ratio
    local hp_ratio = monster.hp / monster.max_hp
    local is_enraged = hp_ratio < config.enrage_threshold

    -- Determine chase range based on enrage state
    local chase_range = config.chase_range
    if is_enraged then
        chase_range = config.enraged_chase_range

        -- Visual feedback for enraged state (first time only)
        if not monster.stats.was_enraged then
            veinborn.add_message(monster.name .. " enters a BERSERK RAGE!")
            veinborn.modify_stat(monster.id, "was_enraged", true)
        end
    end

    -- Calculate distance to player
    local distance = veinborn.ai.distance_to(monster.id, player.id)

    -- Attack if adjacent
    if veinborn.ai.is_adjacent(monster.id, player.id) then
        return {
            action = "attack",
            target_id = player.id
        }
    end

    -- Chase if in range
    if distance <= chase_range then
        return {
            action = "move_towards",
            target_id = player.id
        }
    end

    -- Wander if out of range
    return {action = "wander"}
end
