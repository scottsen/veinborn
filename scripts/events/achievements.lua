-- scripts/events/achievements.lua
--[[
Achievement System for Brogue

This event handler tracks player achievements across multiple event types.
Achievements are tracked in-session (state is lost on game restart).

Achievements:
- Centurion: Kill 100 monsters
- Slayer: Kill 500 monsters
- Explorer: Descend 10 floors
- Deep Diver: Descend 25 floors
- Hoarder: Collect 1000 gold
- Craftsman: Craft 50 items
- Master Craftsman: Craft 100 items
- Survivor: Survive 1000 turns
- Veteran: Survive 5000 turns

Future enhancements:
- Persist achievements to save file
- Track unlock timestamps
- Display achievement progress bar
--]]

-- @subscribe: entity_died, floor_changed, item_crafted, turn_ended
-- @handler: on_entity_died, on_floor_changed, on_item_crafted, on_turn_ended

-- Achievement state
local achievements = {
    -- Combat achievements
    centurion = {unlocked = false, name = "Centurion", desc = "Kill 100 monsters"},
    slayer = {unlocked = false, name = "Slayer", desc = "Kill 500 monsters"},

    -- Exploration achievements
    explorer = {unlocked = false, name = "Explorer", desc = "Descend 10 floors"},
    deep_diver = {unlocked = false, name = "Deep Diver", desc = "Descend 25 floors"},

    -- Resource achievements
    hoarder = {unlocked = false, name = "Hoarder", desc = "Collect 1000 gold"},

    -- Crafting achievements
    craftsman = {unlocked = false, name = "Craftsman", desc = "Craft 50 items"},
    master_craftsman = {unlocked = false, name = "Master Craftsman", desc = "Craft 100 items"},

    -- Survival achievements
    survivor = {unlocked = false, name = "Survivor", desc = "Survive 1000 turns"},
    veteran = {unlocked = false, name = "Veteran", desc = "Survive 5000 turns"},
}

-- Track stats
local stats = {
    player_kills = 0,
    deepest_floor = 1,
    gold_collected = 0,
    items_crafted = 0,
    turns_survived = 0,
}

-- Helper function to unlock achievement
local function unlock_achievement(achievement_id)
    local ach = achievements[achievement_id]
    if ach and not ach.unlocked then
        ach.unlocked = true
        brogue.add_message(string.format(
            "Achievement Unlocked: %s - %s",
            ach.name,
            ach.desc
        ))
        return true
    end
    return false
end

-- Combat achievements
function on_entity_died(event)
    -- Only track player kills
    if event.data.killer_id ~= "player_1" then
        return
    end

    stats.player_kills = stats.player_kills + 1

    -- Check combat achievements
    if stats.player_kills == 100 then
        unlock_achievement("centurion")
    elseif stats.player_kills == 500 then
        unlock_achievement("slayer")
    end

    -- Show milestone messages
    if stats.player_kills % 50 == 0 then
        brogue.add_message(string.format("Total kills: %d", stats.player_kills))
    end
end

-- Exploration achievements
function on_floor_changed(event)
    local to_floor = event.data.to_floor or 1

    -- Track deepest floor reached
    if to_floor > stats.deepest_floor then
        stats.deepest_floor = to_floor

        -- Check exploration achievements
        if stats.deepest_floor == 10 then
            unlock_achievement("explorer")
        elseif stats.deepest_floor == 25 then
            unlock_achievement("deep_diver")
        end

        -- Show milestone messages
        if stats.deepest_floor % 5 == 0 then
            brogue.add_message(string.format("Deepest floor: %d", stats.deepest_floor))
        end
    end
end

-- Crafting achievements
function on_item_crafted(event)
    stats.items_crafted = stats.items_crafted + 1

    -- Check crafting achievements
    if stats.items_crafted == 50 then
        unlock_achievement("craftsman")
    elseif stats.items_crafted == 100 then
        unlock_achievement("master_craftsman")
    end

    -- Show milestone messages
    if stats.items_crafted % 25 == 0 then
        brogue.add_message(string.format("Items crafted: %d", stats.items_crafted))
    end
end

-- Survival achievements
function on_turn_ended(event)
    stats.turns_survived = event.turn

    -- Check survival achievements
    if stats.turns_survived == 1000 then
        unlock_achievement("survivor")
    elseif stats.turns_survived == 5000 then
        unlock_achievement("veteran")
    end

    -- Show progress every 500 turns
    if stats.turns_survived % 500 == 0 and stats.turns_survived > 0 then
        brogue.add_message(string.format("Turns survived: %d", stats.turns_survived))
    end
end

-- Helper function to get achievement progress (for debugging)
function get_achievement_stats()
    local unlocked_count = 0
    for _, ach in pairs(achievements) do
        if ach.unlocked then
            unlocked_count = unlocked_count + 1
        end
    end

    return {
        unlocked = unlocked_count,
        total = 9,
        kills = stats.player_kills,
        floor = stats.deepest_floor,
        crafted = stats.items_crafted,
        turns = stats.turns_survived,
    }
end
