local TERMO_TYPE = "MateArgentino.Termo"
local HOT_THRESHOLD = 1.6
local INSULATION_HOURS = 24
local UPDATE_INTERVAL_TICKS = 30
local HOT_UNTIL_KEY = "MateArgentinoHotUntil"

local tickCounter = 0

local function updateTermo(item)
    if not item or item:getFullType() ~= TERMO_TYPE then
        return
    end

    local container = item:getFluidContainer()
    if not container or container:isEmpty() then
        return
    end

    local hotWater = Fluid.Get("HotWater")
    if not hotWater then
        return
    end

    local amount = container:getAmount()
    local now = getGameTime():getWorldAgeHours()
    local modData = item:getModData()
    local hotUntil = modData[HOT_UNTIL_KEY]

    if item:getItemHeat() > HOT_THRESHOLD and container:isPureFluid(Fluid.Water) then
        container:Empty()
        container:addFluid(hotWater, amount)
        modData[HOT_UNTIL_KEY] = now + INSULATION_HOURS
        item:setItemHeat(2.0)
    elseif container:isPureFluid(hotWater) then
        if not hotUntil then
            hotUntil = now + INSULATION_HOURS
            modData[HOT_UNTIL_KEY] = hotUntil
        end

        if now < hotUntil then
            item:setItemHeat(2.0)
            return
        end

        container:Empty()
        container:addFluid(Fluid.Water, amount)
        modData[HOT_UNTIL_KEY] = nil
        item:setItemHeat(1.0)
    end
end

local function updateInventory(container)
    if not container then
        return
    end

    local items = container:getItems()
    for index = 0, items:size() - 1 do
        local item = items:get(index)
        updateTermo(item)

        if instanceof(item, "InventoryContainer") then
            updateInventory(item:getInventory())
        end
    end
end

local function updatePlayerTermos()
    tickCounter = tickCounter + 1
    if tickCounter < UPDATE_INTERVAL_TICKS then
        return
    end
    tickCounter = 0

    for playerIndex = 0, getNumActivePlayers() - 1 do
        local player = getSpecificPlayer(playerIndex)
        if player then
            updateInventory(player:getInventory())
        end
    end
end

Events.OnTick.Add(updatePlayerTermos)
