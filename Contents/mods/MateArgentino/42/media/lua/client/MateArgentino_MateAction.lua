require "TimedActions/ISCraftAction"

local CEBAR_RECIPES = {
    CebarMate = 0.045,
    CebarMateCaliente = 0.045,
}

local function isCebarAction(action)
    if not action.recipe then
        return false
    end
    local recipeName = action.recipe:getUntranslatedName()
    return CEBAR_RECIPES[recipeName] ~= nil
end

local originalCraftPerform = ISCraftAction.perform

function ISCraftAction:perform()
    originalCraftPerform(self)

    if isCebarAction(self) then
        local amount = CEBAR_RECIPES[self.recipe:getUntranslatedName()]
        if isClient() then
            sendClientCommand("MateArgentino", "ConsumeFluid", {
                playerIndex = self.character:getPlayerNum(),
                amount = tostring(amount),
            })
        end
    end
end
