--[[
Summoner AI - Summons allies, avoids combat

Characteristics:
- Maintains distance from player
- "Summons" nearby monsters periodically
- Flees when player gets close
- Never attacks directly

Suitable for: Necromancers, Shamans, Cultists

Configuration (in ai_behaviors.yaml):
  summoner:
    description: "Summons allies, avoids direct combat"
    summon_distance: 8   # Summon when player within 8 tiles
    flee_distance: 4     # Flee when player within 4 tiles
    summon_cooldown: 10  # Summon every 10 turns
--]]

-- Constants
local SUMMON_DISTANCE = 8  -- Summon when player within 8 tiles
local FLEE_DISTANCE = 4    -- Flee when player within 4 tiles
local SUMMON_COOLDOWN = 10 -- Summon every 10 turns

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

    -- Track turns since last summon
    local last_summon_turn = monster.stats.last_summon_turn or 0
    local current_turn = brogue.get_turn_count()
    local turns_since_summon = current_turn - last_summon_turn

    -- Flee if player too close
    if distance < FLEE_DISTANCE then
        brogue.add_message(monster.name .. " retreats to safety!")
        return {
            action = "flee_from",
            target_id = player.id
        }
    end

    -- Summon if conditions met
    if distance <= SUMMON_DISTANCE and turns_since_summon >= SUMMON_COOLDOWN then
        -- Update summon timestamp
        brogue.modify_stat(monster.id, "last_summon_turn", current_turn)

        -- Visual feedback
        brogue.add_message(monster.name .. " chants an incantation!")

        -- Future: Actually spawn monsters nearby
        -- For now: Just message and cooldown
        return {action = "idle"}
    end

    -- Maintain distance
    if distance < SUMMON_DISTANCE then
        return {
            action = "flee_from",
            target_id = player.id
        }
    end

    -- Wander when safe
    return {action = "wander"}
end
