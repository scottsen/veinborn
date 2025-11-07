-- scripts/events/quest_tracker.lua
--[[
Quest Tracking System for Brogue

This event handler demonstrates how to track quest progress using
multiple event types and maintain quest state.

Example Quest: "Goblin Slayer"
- Objective: Kill 5 goblins
- Reward: 100 gold
- Tracks progress and displays updates

This can be extended to support:
- Multiple active quests
- Quest chains
- Dynamic quest generation
- Time-limited quests
- Quest rewards (items, stats, etc.)
--]]

-- @subscribe: entity_died, game_started
-- @handler: on_entity_died, on_game_started

-- Quest definitions
local quests = {
    goblin_slayer = {
        name = "Goblin Slayer",
        description = "Kill 5 goblins",
        active = true,
        completed = false,
        progress = 0,
        target = 5,
        reward_gold = 100,
        reward_message = "You have proven yourself against the goblin menace!",
    },
    rat_exterminator = {
        name = "Rat Exterminator",
        description = "Kill 10 rats",
        active = false,
        completed = false,
        progress = 0,
        target = 10,
        reward_gold = 50,
        reward_message = "The rat problem is solved!",
    },
}

-- Helper function to check if entity name matches quest target
local function entity_matches_target(entity_name, target)
    -- Case-insensitive match
    local entity_lower = string.lower(entity_name)
    local target_lower = string.lower(target)
    return string.find(entity_lower, target_lower) ~= nil
end

-- Helper function to award quest completion
local function complete_quest(quest_id)
    local quest = quests[quest_id]

    if not quest or quest.completed then
        return false
    end

    quest.completed = true
    quest.active = false

    -- Display completion message
    brogue.add_message("====================")
    brogue.add_message(string.format("Quest Complete: %s", quest.name))
    brogue.add_message(quest.reward_message)

    -- Award gold reward
    if quest.reward_gold > 0 then
        brogue.add_message(string.format("Reward: +%d gold", quest.reward_gold))
        -- Note: Would need brogue.modify_stat("player_1", "gold", quest.reward_gold)
        -- if gold stat exists
    end

    brogue.add_message("====================")

    return true
end

-- Helper function to update quest progress
local function update_quest_progress(quest_id, entity_name, target_name)
    local quest = quests[quest_id]

    if not quest or not quest.active or quest.completed then
        return false
    end

    if entity_matches_target(entity_name, target_name) then
        quest.progress = quest.progress + 1

        -- Display progress update
        brogue.add_message(string.format(
            "Quest: %s [%d/%d]",
            quest.name,
            quest.progress,
            quest.target
        ))

        -- Check if quest is complete
        if quest.progress >= quest.target then
            complete_quest(quest_id)
        end

        return true
    end

    return false
end

-- Event handler for entity deaths
function on_entity_died(event)
    -- Only track player kills
    if event.data.killer_id ~= "player_1" then
        return
    end

    local entity_name = event.data.entity_name or ""

    -- Update all active quests
    update_quest_progress("goblin_slayer", entity_name, "goblin")
    update_quest_progress("rat_exterminator", entity_name, "rat")
end

-- Event handler for game start
function on_game_started(event)
    -- Activate starting quest
    quests.goblin_slayer.active = true

    brogue.add_message("New Quest: " .. quests.goblin_slayer.name)
    brogue.add_message(quests.goblin_slayer.description)
end

-- Helper function to get quest status (for debugging)
function get_quest_status()
    local status = {}

    for quest_id, quest in pairs(quests) do
        status[quest_id] = {
            name = quest.name,
            active = quest.active,
            completed = quest.completed,
            progress = quest.progress,
            target = quest.target,
        }
    end

    return status
end

-- Helper function to activate a quest (could be called from actions)
function activate_quest(quest_id)
    local quest = quests[quest_id]

    if not quest or quest.completed then
        return false
    end

    quest.active = true
    brogue.add_message("New Quest: " .. quest.name)
    brogue.add_message(quest.description)

    return true
end
