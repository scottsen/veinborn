--[[
AI Behavior Template

Use this template as a starting point for creating custom AI behaviors.

Instructions:
1. Copy this file to scripts/ai/your_behavior.lua
2. Update the description and configuration
3. Implement the update() function logic
4. Add configuration to data/balance/ai_behaviors.yaml
5. Register in game code: ai_system.register_lua_behavior("your_behavior", "scripts/ai/your_behavior.lua")

Configuration example (in ai_behaviors.yaml):
  your_behavior:
    description: "Description of your AI behavior"
    chase_range: 10
    custom_param: value
--]]

-- Behavior update function
-- Called each turn for monsters with ai_type matching this behavior
-- @param monster: Monster entity table with properties:
--   - id: Entity ID
--   - name: Monster name
--   - x, y: Position
--   - hp, max_hp: Health
--   - attack, defense: Combat stats
--   - stats: Custom stats dictionary
-- @param config: Behavior configuration from YAML
-- @return: Action descriptor table
function update(monster, config)
    -- Get player (primary target)
    local player = veinborn.get_player()

    -- Check if player exists and is alive
    if not player or not player.is_alive then
        return {action = "wander"}
    end

    -- Example: Calculate distance to player
    local distance = veinborn.ai.distance_to(monster.id, player.id)

    -- Example: Check if adjacent
    local is_adjacent = veinborn.ai.is_adjacent(monster.id, player.id)

    -- TODO: Implement your AI logic here
    -- Use the veinborn.ai.* helper methods to make decisions

    -- Example decision tree:
    if is_adjacent then
        -- Attack when adjacent
        return {
            action = "attack",
            target_id = player.id
        }
    elseif distance <= 10 then
        -- Chase when in range
        return {
            action = "move_towards",
            target_id = player.id
        }
    else
        -- Wander when out of range
        return {action = "wander"}
    end
end
