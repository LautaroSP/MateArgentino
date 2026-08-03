local NEXT_DRY_MATE = {}
local EMPTY_THRESHOLD = 0.0001
for remaining = 1, 40 do
    local nextType = remaining > 1
        and ("MateArgentino.MateConYerba" .. (remaining - 1))
        or "MateArgentino.MateLavado"

    NEXT_DRY_MATE["MateArgentino.MatePreparado" .. remaining] = nextType
    NEXT_DRY_MATE["MateArgentino.MatePreparadoCaliente" .. remaining] = nextType
end

local function recoverEmptyMates(container)
    if not container then
        return
    end

    local items = container:getItems()
    for index = items:size() - 1, 0, -1 do
        local item = items:get(index)

        if instanceof(item, "InventoryContainer") then
            recoverEmptyMates(item:getInventory())
        end

        local nextType = NEXT_DRY_MATE[item:getFullType()]
        local fluidContainer = nextType and item:getFluidContainer()
        local actionFinished = item:getJobDelta() <= 0
        local isEmpty = fluidContainer
            and (fluidContainer:isEmpty()
                or fluidContainer:getAmount() <= EMPTY_THRESHOLD)

        if actionFinished and isEmpty then
            local favorite = item:isFavorite()
            container:Remove(item)

            local dryMate = container:AddItem(nextType)
            if dryMate then
                dryMate:setFavorite(favorite)
            end

            triggerEvent("OnContainerUpdate")
        end
    end
end

local recoveryTick = 0
local function recoverPlayerMates()
    recoveryTick = recoveryTick + 1
    if recoveryTick < 10 then
        return
    end
    recoveryTick = 0

    for playerIndex = 0, getNumActivePlayers() - 1 do
        local player = getSpecificPlayer(playerIndex)
        if player then
            recoverEmptyMates(player:getInventory())
        end
    end
end

Events.OnTick.Add(recoverPlayerMates)
