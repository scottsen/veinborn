--[[
Lua Action Template

This is a template for creating custom actions in Brogue.
Copy this file and modify it to create your own actions.

File location: scripts/actions/your_action_name.lua

To register your action:
    factory.register_lua_action(
        "your_action",
        "actions/your_action_name.lua",
        lua_runtime,
        "Description of your action"
    )
--]]

-- ============================================================================
-- Configuration Constants
-- ============================================================================

local PARAMETER_1 = 10
local PARAMETER_2 = 5

-- ============================================================================
-- Validation Function
-- ============================================================================
-- This function checks if the action can be executed.
-- Return true if valid, false otherwise.
-- Use brogue.add_message() to inform the player why validation failed.

function validate(actor_id, params)
    -- Get the player entity
    local player = brogue.get_player()

    -- Example: Check player has enough resources
    local current_mana = player.stats.mana or 0
    if current_mana < PARAMETER_1 then
        brogue.add_message("Not enough mana!")
        return false
    end

    -- Example: Check required parameters
    if not params.target_x or not params.target_y then
        brogue.add_message("Target coordinates required!")
        return false
    end

    -- Example: Check range
    local dx = params.target_x - player.x
    local dy = params.target_y - player.y
    local dist = math.sqrt(dx * dx + dy * dy)
    if dist > PARAMETER_2 then
        brogue.add_message("Target out of range!")
        return false
    end

    -- Validation passed
    return true
end

-- ============================================================================
-- Execution Function
-- ============================================================================
-- This function executes the action and returns an outcome.
-- Return a table with: success, took_turn, messages, events

function execute(actor_id, params)
    local player = brogue.get_player()

    -- Perform action effects
    -- Example: Deduct resources
    brogue.modify_stat(actor_id, "mana", -PARAMETER_1)

    -- Example: Add messages
    brogue.add_message("Action executed successfully!")

    -- Example: Affect entities
    local target_x = params.target_x
    local target_y = params.target_y
    local targets = brogue.get_entities_in_range(target_x, target_y, 2)

    local events = {}
    for i = 1, #targets do
        local target = targets[i]
        if target.entity_type == "MONSTER" then
            brogue.modify_stat(target.id, "hp", -10)
            table.insert(events, {
                type = "damage",
                target_id = target.id,
                amount = 10
            })
        end
    end

    -- Return outcome
    return {
        success = true,        -- Did the action succeed?
        took_turn = true,      -- Does this consume a turn?
        messages = {},         -- Additional messages (or use brogue.add_message)
        events = events        -- Events for logging/pub-sub system
    }
end
