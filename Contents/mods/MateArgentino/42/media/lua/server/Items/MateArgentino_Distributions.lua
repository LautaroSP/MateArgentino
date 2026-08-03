require "Items/ProceduralDistributions"

local function addItem(distributionName, itemType, weight)
    local distribution = ProceduralDistributions.list[distributionName]
    if not distribution or not distribution.items then
        print("MateArgentino: distribución inexistente: " .. distributionName)
        return
    end

    table.insert(distribution.items, itemType)
    table.insert(distribution.items, weight)
end

local qualities = {
    -- La suma de los pesos conserva la rareza anterior: 50% económica,
    -- 35% media y 15% premium. Cada paquete ya trae sorteado su rendimiento.
    { name = "Economica", minimum = 10, maximum = 15, share = 0.50 },
    { name = "Media", minimum = 15, maximum = 25, share = 0.35 },
    { name = "Premium", minimum = 25, maximum = 40, share = 0.15 },
}

local function addRandomizedYerba(distributionName, totalWeight)
    for _, quality in ipairs(qualities) do
        local variants = quality.maximum - quality.minimum + 1
        local variantWeight = totalWeight * quality.share / variants
        for cebadas = quality.minimum, quality.maximum do
            addItem(
                distributionName,
                "MateArgentino.Yerba" .. quality.name .. cebadas,
                variantWeight
            )
        end
    end
end

-- La yerba es relativamente rara en Kentucky.
addRandomizedYerba("KitchenDryFood", 1.5)
addRandomizedYerba("GigamartDryGoods", 3.0)
addRandomizedYerba("CafeKitchenTea", 1.0)

-- Los utensilios aparecen en cocinas y comercios.
addItem("KitchenDishes", "MateArgentino.MateVacio", 1.0)
addItem("GigamartHousewares", "MateArgentino.MateVacio", 2.0)
addItem("KitchenBottles", "MateArgentino.Termo", 0.8)
addItem("GigamartHousewares", "MateArgentino.Termo", 1.5)
addItem("CampingStoreGear", "MateArgentino.Termo", 1.0)

print("MateArgentino: distribuciones cargadas")
