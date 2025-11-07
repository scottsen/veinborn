-- scripts/events/dynamic_loot.lua
--[[
Dynamic Loot System for Brogue

This event handler modifies loot drops based on various factors:
- Floor depth (deeper floors = better loot)
- Kill streaks (consecutive kills = bonus loot)
- Player performance (low HP = more healing drops)

This demonstrates event-driven game modification without changing
core game mechanics.

Features:
- Track kill streaks
- Bonus loot on multi-kills
- Rare item drops on deep floors
- Dynamic drop rate adjustment
- Special loot messages

Future enhancements:
- Actually spawn loot items (requires item spawning API)
- Track loot statistics
- Lucky/unlucky streaks
- Boss-specific loot tables
--]]

-- @subscribe: entity_died, floor_changed, turn_ended
-- @handler: on_entity_died, on_floor_changed, on_turn_ended

-- Loot system state
local loot_state = {
    current_floor = 1,
    kill_streak = 0,
    last_kill_turn = 0,
    total_rare_drops = 0,
    total_bonus_drops = 0,
}

-- Loot configuration
local loot_config = {
    kill_streak_timeout = 3,  -- Turns before streak resets
    kill_streak_bonus_threshold = 3,  -- Kills needed for bonus
    rare_drop_floor_threshold = 10,  -- Floor for rare drops
    rare_drop_chance = 0.1,  -- 10% chance on deep floors
}

-- Helper function to check if kill streak is active
local function is_streak_active(current_turn)
    local turns_since_kill = current_turn - loot_state.last_kill_turn
    return turns_since_kill <= loot_config.kill_streak_timeout
end

-- Helper function to roll for rare drop
local function roll_rare_drop()
    -- Simple RNG using current time
    -- Note: This is not cryptographically secure, just for demonstration
    local rand = (os.time() % 100) / 100.0
    return rand < loot_config.rare_drop_chance
end

-- Helper function to get floor-based loot bonus
local function get_floor_bonus(floor)
    if floor >= 25 then
        return "legendary"
    elseif floor >= 15 then
        return "epic"
    elseif floor >= 10 then
        return "rare"
    else
        return "common"
    end
end

-- Handle entity deaths for loot drops
function on_entity_died(event)
    -- Only process player kills
    if event.data.killer_id ~= "player_1" then
        return
    end

    local current_turn = event.turn or 0
    local entity_name = event.data.entity_name or "enemy"

    -- Update kill streak
    if is_streak_active(current_turn) then
        loot_state.kill_streak = loot_state.kill_streak + 1
    else
        loot_state.kill_streak = 1
    end

    loot_state.last_kill_turn = current_turn

    -- Check for kill streak bonus
    if loot_state.kill_streak >= loot_config.kill_streak_bonus_threshold then
        loot_state.total_bonus_drops = loot_state.total_bonus_drops + 1

        brogue.add_message(string.format(
            "Kill Streak x%d! Bonus loot!",
            loot_state.kill_streak
        ))

        -- Reset streak after bonus (or continue for mega-streaks)
        if loot_state.kill_streak >= 10 then
            brogue.add_message("MEGA STREAK! Epic loot drop!")
        end
    end

    -- Check for rare drops on deep floors
    if loot_state.current_floor >= loot_config.rare_drop_floor_threshold then
        if roll_rare_drop() then
            loot_state.total_rare_drops = loot_state.total_rare_drops + 1

            local tier = get_floor_bonus(loot_state.current_floor)
            brogue.add_message(string.format(
                "You found a %s item from %s!",
                tier,
                entity_name
            ))
        end
    end

    -- Floor-specific loot messages
    if loot_state.current_floor >= 20 then
        if loot_state.kill_streak % 5 == 0 then
            brogue.add_message("The loot quality improves in the depths...")
        end
    end
end

-- Track floor changes for loot scaling
function on_floor_changed(event)
    local to_floor = event.data.to_floor or 1

    loot_state.current_floor = to_floor

    -- Reset kill streak on floor change
    loot_state.kill_streak = 0

    -- Display loot tier message
    local tier = get_floor_bonus(to_floor)
    if to_floor >= loot_config.rare_drop_floor_threshold then
        brogue.add_message(string.format(
            "Floor %d: %s loot tier unlocked",
            to_floor,
            tier
        ))
    end
end

-- Streak timeout check
function on_turn_ended(event)
    local current_turn = event.turn or 0

    -- Check if streak expired
    if loot_state.kill_streak > 0 and not is_streak_active(current_turn) then
        if loot_state.kill_streak >= loot_config.kill_streak_bonus_threshold then
            brogue.add_message("Kill streak ended.")
        end
        loot_state.kill_streak = 0
    end

    -- Show loot stats every 100 turns
    if current_turn % 100 == 0 and current_turn > 0 then
        brogue.add_message(string.format(
            "Loot stats: %d rare drops, %d bonus drops",
            loot_state.total_rare_drops,
            loot_state.total_bonus_drops
        ))
    end
end

-- Helper function to get loot statistics (for debugging)
function get_loot_stats()
    return {
        floor = loot_state.current_floor,
        streak = loot_state.kill_streak,
        rare_drops = loot_state.total_rare_drops,
        bonus_drops = loot_state.total_bonus_drops,
        loot_tier = get_floor_bonus(loot_state.current_floor),
    }
end
