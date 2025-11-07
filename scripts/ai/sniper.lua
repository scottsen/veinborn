--[[
Sniper AI - Maintains range, attacks from distance

Characteristics:
- Prefers to stay at medium range (4-6 tiles)
- Moves away if player too close (<4 tiles)
- "Attacks" when in ideal range (4-6 tiles)
- Flees when cornered or low HP

Suitable for: Archers, Ranged enemies

Configuration (in ai_behaviors.yaml):
  sniper:
    description: "Ranged attacker, maintains distance"
    ideal_range_min: 4
    ideal_range_max: 6
    flee_threshold: 0.3
--]]

-- Constants
local IDEAL_RANGE_MIN = 4
local IDEAL_RANGE_MAX = 6
local FLEE_THRESHOLD = 0.3

-- Behavior update function
-- @param monster: Monster entity table
-- @param config: Behavior configuration from YAML
-- @return: Action descriptor
function update(monster, config)
    local player = brogue.get_player()

    if not player or not player.is_alive then
        return {action = "wander"}
    end

    local distance = brogue.ai.distance_to(monster.id, player.id)
    local hp_ratio = monster.hp / monster.max_hp

    -- Flee if low HP
    if hp_ratio < FLEE_THRESHOLD then
        return {
            action = "flee_from",
            target_id = player.id
        }
    end

    -- Too close - back away
    if distance < IDEAL_RANGE_MIN then
        return {
            action = "flee_from",
            target_id = player.id
        }
    end

    -- In ideal range - "attack" (for now just simulate)
    if distance >= IDEAL_RANGE_MIN and distance <= IDEAL_RANGE_MAX then
        -- Future: Create projectile action
        -- For now: message + stay in position
        brogue.add_message(monster.name .. " takes aim from afar!")
        return {action = "idle"}
    end

    -- Too far - move closer (but not too close)
    if distance > IDEAL_RANGE_MAX then
        return {
            action = "move_towards",
            target_id = player.id
        }
    end

    return {action = "idle"}
end
