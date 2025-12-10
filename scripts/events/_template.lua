-- scripts/events/_template.lua
--[[
Lua Event Handler Template

This template shows how to create event handlers for Veinborn.

Event handlers react to game events like entity deaths, item crafting,
floor changes, etc. They enable achievements, quests, dynamic systems,
and custom game modes.

Usage:
1. Copy this template to scripts/events/your_handler.lua
2. Implement handler functions for events you care about
3. Add @subscribe annotation for auto-loading
4. Restart game to load handler

Event Types Available:
- entity_died, entity_damaged, entity_healed
- attack_resolved
- item_crafted, item_picked_up, item_dropped
- floor_changed, floor_generated
- turn_started, turn_ended
- game_started, game_over
- (see docs/EVENT_SYSTEM.md for complete list)
--]]

-- @subscribe: entity_died, item_crafted
-- @handler: on_entity_died, on_item_crafted

-- State persistence (survives across handler calls)
local state = {
    kills = 0,
    items_crafted = 0,
}

-- Handler for entity_died events
function on_entity_died(event)
    -- Event structure:
    -- event.type = "entity_died"
    -- event.data = {entity_id, entity_name, killer_id, cause}
    -- event.turn = current turn number
    -- event.timestamp = time in seconds

    if event.data.killer_id == "player_1" then
        state.kills = state.kills + 1
        veinborn.add_message("Kills: " .. state.kills)
    end
end

-- Handler for item_crafted events
function on_item_crafted(event)
    state.items_crafted = state.items_crafted + 1
    veinborn.add_message("Items crafted: " .. state.items_crafted)
end

-- Error handling example
function on_error_prone_event(event)
    -- Wrap risky code in pcall
    local success, err = pcall(function()
        -- Your code here
        local entity = veinborn.get_entity(event.data.entity_id)
        -- ...
    end)

    if not success then
        veinborn.add_message("Error in event handler: " .. err)
    end
end

-- Multi-event coordination example
-- Track both deaths and healing to calculate net damage
local damage_stats = {
    total_damage = 0,
    total_healing = 0,
}

function on_entity_damaged(event)
    damage_stats.total_damage = damage_stats.total_damage + (event.data.amount or 0)
end

function on_entity_healed(event)
    damage_stats.total_healing = damage_stats.total_healing + (event.data.amount or 0)
end

function on_turn_ended(event)
    -- Report stats every 100 turns
    if event.turn % 100 == 0 then
        local net = damage_stats.total_damage - damage_stats.total_healing
        veinborn.add_message(string.format(
            "Stats: %d damage, %d healing, %d net",
            damage_stats.total_damage,
            damage_stats.total_healing,
            net
        ))
    end
end

--[[
    Testing Support

    For unit tests, export your state with a getter function.
    This allows tests to verify internal state without breaking encapsulation.
--]]

--- Export handler state for testing
-- @return table Handler state with all tracked values
function get_handler_state()
    return {
        -- Export only what tests need to verify
        kills = state.kills,
        items_crafted = state.items_crafted,
        -- Can also export nested state
        damage_stats = damage_stats
    }
end
