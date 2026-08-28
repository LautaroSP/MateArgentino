local TERMO_TYPE = "MateArgentino.Termo"

local function findTermo(player)
    local inventory = player:getInventory()
    local items = inventory:getItems()
    for i = 0, items:size() - 1 do
        local item = items:get(i)
        if item:getFullType() == TERMO_TYPE then
            return item
        end
    end
    return nil
end

local function onConsumeFluid(player, args)
    if not player then
        return
    end

    local amount = tonumber(args.amount) or 0.045
    local termo = findTermo(player)
    if not termo then
        return
    end

    local container = termo:getFluidContainer()
    if not container or container:isEmpty() then
        return
    end

    container:removeFluid(amount)
end

local function onRecoverMate(player, args)
    if not player then
        return
    end

    local fullType = args.fullType
    local nextType = args.nextType or "MateArgentino.MateLavado"
    local inventory = player:getInventory()
    local items = inventory:getItems()
    for i = items:size() - 1, 0, -1 do
        local item = items:get(i)
        if item:getFullType() == fullType then
            local fluidContainer = item:getFluidContainer()
            local isEmpty = fluidContainer
                and (fluidContainer:isEmpty()
                    or fluidContainer:getAmount() <= 0.0001)

            if isEmpty then
                local favorite = item:isFavorite()
                inventory:Remove(item)
                local dryMate = inventory:AddItem(nextType)
                if dryMate then
                    dryMate:setFavorite(favorite)
                end
                break
            end
        end
    end
end

if not MateArgentino_ServerInstalled then
    MateArgentino_ServerInstalled = true

    local commands = {
        ConsumeFluid = onConsumeFluid,
        RecoverMate = onRecoverMate,
    }

    Events.OnClientCommand.Add(function(module, command, args)
        if module ~= "MateArgentino" then
            return
        end
        local handler = commands[command]
        if handler then
            local player = args and args.playerIndex
                and getSpecificPlayer(args.playerIndex)
            handler(player, args or {})
        end
    end)
end
