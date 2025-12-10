--[[
Fireball Action - AOE damage spell

This is an example Lua action that demonstrates:
- Mana cost checking
- Range validation
- Area-of-effect damage
- Event generation
- Message logging

Requirements:
- Costs 10 mana
- Range: 5 tiles
- AOE radius: 2 tiles
- Base damage: 15

Usage:
    factory.create("fireball", actor_id="player_1", x=10, y=10)
--]]

-- Configuration
local MANA_COST = 10
local RANGE = 5
local AOE_RADIUS = 2
local BASE_DAMAGE = 15

-- Validate if fireball can be cast
function validate(actor_id, params)
    local player = veinborn.get_player()

    -- Check if target coordinates provided
    if not params.x or not params.y then
        veinborn.add_message("Fireball requires target coordinates!")
        return false
    end

    local target_x = params.x
    local target_y = params.y

    -- Check if player has enough mana
    local current_mana = player.stats.mana or 0
    if current_mana < MANA_COST then
        veinborn.add_message("Not enough mana for Fireball! (Need " .. MANA_COST .. ", have " .. current_mana .. ")")
        return false
    end

    -- Check if target is in range
    local dx = target_x - player.x
    local dy = target_y - player.y
    local dist = math.sqrt(dx * dx + dy * dy)

    if dist > RANGE then
        veinborn.add_message("Target too far away! (Range: " .. RANGE .. ")")
        return false
    end

    -- Check if target is in bounds
    if not veinborn.in_bounds(target_x, target_y) then
        veinborn.add_message("Target out of bounds!")
        return false
    end

    return true
end

-- Execute fireball spell
function execute(actor_id, params)
    local player = veinborn.get_player()
    local target_x = params.x
    local target_y = params.y

    -- Deduct mana cost
    veinborn.modify_stat(actor_id, "mana", -MANA_COST)

    -- Visual effect message
    veinborn.add_message("A blazing fireball erupts at (" .. target_x .. ", " .. target_y .. ")!")

    -- Get all entities in AOE
    local targets = veinborn.get_entities_in_range(target_x, target_y, AOE_RADIUS)

    local events = {}
    local hit_count = 0
    local total_damage = 0

    -- Process each target in AOE
    for i = 1, #targets do
        local target = targets[i]

        -- Only damage monsters (not the player or other entities)
        if target.entity_type == "MONSTER" and target.is_alive then
            -- Calculate damage (could add damage variance here)
            local damage = BASE_DAMAGE

            -- Deal damage
            veinborn.modify_stat(target.id, "hp", -damage)

            -- Create damage event
            table.insert(events, {
                type = "damage",
                source = "fireball",
                target_id = target.id,
                target_name = target.name,
                amount = damage
            })

            -- Combat message
            veinborn.add_message("  " .. target.name .. " takes " .. damage .. " fire damage!")

            hit_count = hit_count + 1
            total_damage = total_damage + damage

            -- Check if target died
            if not veinborn.is_alive(target.id) then
                veinborn.add_message("  " .. target.name .. " is incinerated!")
                table.insert(events, {
                    type = "death",
                    source = "fireball",
                    target_id = target.id,
                    target_name = target.name
                })
            end
        end
    end

    -- Summary message
    if hit_count > 0 then
        veinborn.add_message("Fireball hit " .. hit_count .. " enemies for " .. total_damage .. " total damage!")
    else
        veinborn.add_message("The fireball explodes harmlessly.")
    end

    -- Create spell cast event
    table.insert(events, {
        type = "spell_cast",
        spell = "fireball",
        caster_id = actor_id,
        target_x = target_x,
        target_y = target_y,
        mana_cost = MANA_COST,
        hit_count = hit_count
    })

    -- Return action outcome
    return {
        success = true,
        took_turn = true,
        messages = {},  -- Messages already added via veinborn.add_message()
        events = events
    }
end
