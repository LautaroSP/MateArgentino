require "TimedActions/ISDrinkFluidAction"
require "TimedActions/ISDrinkFromBottle"

-- Bob_MateSip has 125 frames. The mate reaches the mouth around frame 42 and
-- starts going down around frame 82, so the loop should only be audible there.
local MATE_SOUND = "MateArgentino_RuidoMate"

local function isMateAction(action)
    if action.eatSound == MATE_SOUND then
        return true
    end
    return action.item ~= nil
        and action.item.getFoodType ~= nil
        and action.item:getFoodType() == "mate"
end

local function stopMateSound(action)
    if action.eatAudio ~= nil and action.eatAudio ~= 0 then
        local emitter = action.character:getEmitter()
        if emitter:isPlaying(action.eatAudio) then
            action.character:stopOrTriggerSound(action.eatAudio)
        end
        action.eatAudio = 0
    end
end

local function startMateSound(action)
    local emitter = action.character:getEmitter()
    if action.eatAudio == nil
        or action.eatAudio == 0
        or not emitter:isPlaying(action.eatAudio) then
        action.eatAudio = emitter:playSound(MATE_SOUND)
    end
end

local function installSoundSync(actionClass)
    local originalStart = actionClass.start
    local originalAnimEvent = actionClass.animEvent
    local originalStop = actionClass.stop
    local originalPerform = actionClass.perform

    function actionClass:start()
        if not isMateAction(self) then
            return originalStart(self)
        end

        -- Prevent the vanilla action from starting the loop immediately.
        local configuredSound = self.eatSound
        self.eatSound = ""
        originalStart(self)
        self.eatSound = configuredSound
        self.eatAudio = 0
    end

    function actionClass:animEvent(event, parameter)
        if isMateAction(self) then
            if event == "MateSoundStart" then
                startMateSound(self)
            elseif event == "MateSoundStop" then
                stopMateSound(self)
            end
        end
        if originalAnimEvent ~= nil then
            return originalAnimEvent(self, event, parameter)
        end
    end

    function actionClass:stop()
        if isMateAction(self) then
            stopMateSound(self)
        end
        return originalStop(self)
    end

    function actionClass:perform()
        if isMateAction(self) then
            stopMateSound(self)
        end
        return originalPerform(self)
    end
end

if not MateArgentino_SoundSyncInstalled then
    MateArgentino_SoundSyncInstalled = true
    installSoundSync(ISDrinkFluidAction)
    installSoundSync(ISDrinkFromBottle)
end
