from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MOD = ROOT / "Contents" / "mods" / "MateArgentino" / "42"
MEDIA = MOD / "media"
SCRIPTS = MEDIA / "scripts"
TRANSLATE = MEDIA / "lua" / "shared" / "Translate"

MAX_CEBADAS = 40
QUALITIES = {
    "Economica": {
        "minimum": 10,
        "maximum": 15,
        "default": 12,
        "icon": "Yerba",
        "es": "Yerba económica",
        "en": "Economy yerba",
    },
    "Media": {
        "minimum": 15,
        "maximum": 25,
        "default": 20,
        "icon": "YerbaMedia",
        "es": "Yerba de calidad media",
        "en": "Medium-quality yerba",
    },
    "Premium": {
        "minimum": 25,
        "maximum": 40,
        "default": 32,
        "icon": "YerbaPremium",
        "es": "Yerba premium",
        "en": "Premium yerba",
    },
}


def yerba_ids() -> list[tuple[str, str, int]]:
    values: list[tuple[str, str, int]] = [("Yerba", "Economica", 12)]
    for quality, data in QUALITIES.items():
        values.append((f"Yerba{quality}", quality, data["default"]))
        for count in range(data["minimum"], data["maximum"] + 1):
            values.append((f"Yerba{quality}{count}", quality, count))
    return values


def item_block(item_id: str, body: list[str]) -> str:
    lines = [f"    item {item_id}", "    {"]
    lines.extend(f"        {line}" for line in body)
    lines.extend(["    }", ""])
    return "\n".join(lines)


def make_items() -> str:
    parts = ["module MateArgentino", "{", ""]

    for item_id, quality, _count in yerba_ids():
        data = QUALITIES[quality]
        tooltip = f"Tooltip_MateArgentino_Yerba{quality}"
        parts.append(
            item_block(
                item_id,
                [
                    "DisplayCategory = Food,",
                    "ItemType = base:food,",
                    "Weight = 0.5,",
                    f"Icon = {data['icon']},",
                    f"WorldStaticModel = MateArgentino.MateArgentino_Yerba{quality}3D,",
                    "FoodType = Yerba,",
                    "Packaged = true,",
                    "HungerChange = -25.0,",
                    "ThirstChange = 40.0,",
                    "fatigueChange = -20.0,",
                    "UnhappyChange = 10,",
                    "Calories = 15.0,",
                    "Carbohydrates = 3.0,",
                    "Lipids = 0.0,",
                    "Proteins = 1.0,",
                    "CantEat = true,",
                    f"Tooltip = {tooltip},",
                ],
            )
        )

    parts.append(
        item_block(
            "MateVacio",
            [
                "DisplayCategory = Cooking,",
                "ItemType = base:normal,",
                "Weight = 0.2,",
                "Icon = MateVacio,",
                "StaticModel = MateArgentino.MateArgentino_MateVacio3D,",
                "WorldStaticModel = MateArgentino.MateArgentino_MateVacio3D,",
                "Tooltip = Tooltip_MateArgentino_MateVacio,",
            ],
        )
    )

    for count in range(1, MAX_CEBADAS + 1):
        parts.append(
            item_block(
                f"MateConYerba{count}",
                [
                    "DisplayCategory = Cooking,",
                    "ItemType = base:normal,",
                    "Weight = 0.3,",
                    "Icon = MatePreparado,",
                    "StaticModel = MateArgentino.MateArgentino_MateConYerba3D,",
                    "WorldStaticModel = MateArgentino.MateArgentino_MateConYerba3D,",
                    f"Tooltip = Tooltip_MateArgentino_Restantes{count},",
                ],
            )
        )

    parts.append(
        item_block(
            "MateLavado",
            [
                "DisplayCategory = Cooking,",
                "ItemType = base:normal,",
                "Weight = 0.3,",
                "Icon = MateLavado,",
                "StaticModel = MateArgentino.MateArgentino_MateLavado3D,",
                "WorldStaticModel = MateArgentino.MateArgentino_MateLavado3D,",
                "Tooltip = Tooltip_MateArgentino_MateLavado,",
            ],
        )
    )

    for count in range(1, MAX_CEBADAS + 1):
        parts.append(
            item_block(
                f"MatePreparado{count}",
                [
                    "DisplayCategory = WaterContainer,",
                    "ItemType = base:normal,",
                    "Weight = 0.5,",
                    "Icon = MatePreparado,",
                    "StaticModel = MateArgentino.MateArgentino_MatePreparado3D,",
                    "WorldStaticModel = MateArgentino.MateArgentino_MatePreparado3D,",
                    "EatType = Mate,",
                    f"Tooltip = Tooltip_MateArgentino_Preparado{count},",
                    "",
                    "component FluidContainer",
                    "{",
                    "    ContainerName = Mate,",
                    "    Capacity = 0.045,",
                    "    TransferRate = 0.045,",
                    "    CustomDrinkSound = MateArgentino_RuidoMate,",
                    "    Fluids",
                    "    {",
                    "        fluid = MateInfusion:0.045,",
                    "    }",
                    "}",
                ],
            )
        )

    for count in range(1, MAX_CEBADAS + 1):
        parts.append(
            item_block(
                f"MatePreparadoCaliente{count}",
                [
                    "DisplayCategory = WaterContainer,",
                    "ItemType = base:normal,",
                    "Weight = 0.5,",
                    "Icon = MatePreparado,",
                    "StaticModel = MateArgentino.MateArgentino_MatePreparado3D,",
                    "WorldStaticModel = MateArgentino.MateArgentino_MatePreparado3D,",
                    "EatType = Mate,",
                    f"Tooltip = Tooltip_MateArgentino_PreparadoCaliente{count},",
                    "",
                    "component FluidContainer",
                    "{",
                    "    ContainerName = Mate,",
                    "    Capacity = 0.045,",
                    "    TransferRate = 0.045,",
                    "    CustomDrinkSound = MateArgentino_RuidoMate,",
                    "    Fluids",
                    "    {",
                    "        fluid = MateInfusionHot:0.045,",
                    "    }",
                    "}",
                ],
            )
        )

    parts.append(
        item_block(
            "Termo",
            [
                "DisplayCategory = WaterContainer,",
                "ItemType = base:normal,",
                "Weight = 0.8,",
                "Icon = Termo,",
                "StaticModel = MateArgentino.MateArgentino_Termo3D,",
                "WorldStaticModel = MateArgentino.MateArgentino_Termo3D,",
                "FillFromDispenserSound = GetWaterFromDispenserMetalMedium,",
                "FillFromLakeSound = GetWaterFromLakeBottle,",
                "FillFromTapSound = GetWaterFromTapMetalMedium,",
                "FillFromToiletSound = GetWaterFromToilet,",
                "CookingSound = BoilingFood,",
                "Tags = base:cookable,",
                "Tooltip = Tooltip_MateArgentino_Termo,",
                "",
                "component FluidContainer",
                "{",
                "    ContainerName = Termo,",
                "    Capacity = 1.0,",
                "    TransferRate = 1.0,",
                "    CustomDrinkSound = DrinkingFromBottle,",
                "}",
            ],
        )
    )
    parts.append("}")
    return "\n".join(parts) + "\n"


def make_recipes() -> str:
    yerbas = yerba_ids()
    yerba_input = ";".join(f"MateArgentino.{item_id}" for item_id, _, _ in yerbas)
    dry_input = ";".join(
        f"MateArgentino.MateConYerba{count}"
        for count in range(MAX_CEBADAS, 0, -1)
    )
    load_map = "\n".join(
        f"            MateArgentino.MateConYerba{count} = MateArgentino.{item_id},"
        for item_id, _quality, count in yerbas
    )
    pour_map = "\n".join(
        f"            MateArgentino.MatePreparado{count} = "
        f"MateArgentino.MateConYerba{count},"
        for count in range(MAX_CEBADAS, 0, -1)
    )
    hot_pour_map = "\n".join(
        f"            MateArgentino.MatePreparadoCaliente{count} = "
        f"MateArgentino.MateConYerba{count},"
        for count in range(MAX_CEBADAS, 0, -1)
    )
    return f"""module MateArgentino
{{
    craftRecipe CargarYerbaMate
    {{
        timedAction = Making,
        time = 30,
        AllowBatchCraft = false,
        Tags = InHandCraft;Cooking;CanBeDoneInDark,
        category = Cooking,
        inputs
        {{
            item 1 [MateArgentino.MateVacio] mode:destroy flags[Prop1],
            item 1 [{yerba_input}] mode:destroy flags[Prop2] mappers[yerbaState],
        }}
        outputs
        {{
            item 1 mapper:yerbaState,
        }}
        itemMapper yerbaState
        {{
{load_map}
        }}
    }}

    craftRecipe CebarMate
    {{
        timedAction = Making,
        time = 20,
        AllowBatchCraft = false,
        Tags = InHandCraft;Cooking,
        category = Cooking,
        inputs
        {{
            item 1 [{dry_input}] mode:destroy flags[Prop2] mappers[mateState],
            item 1 [MateArgentino.Termo] mode:keep flags[NotEmpty;Prop1],
            -fluid 0.045 [Water],
        }}
        outputs
        {{
            item 1 mapper:mateState,
        }}
        itemMapper mateState
        {{
{pour_map}
        }}
    }}

    craftRecipe CebarMateCaliente
    {{
        timedAction = Making,
        time = 20,
        AllowBatchCraft = false,
        Tags = InHandCraft;Cooking,
        category = Cooking,
        inputs
        {{
            item 1 [{dry_input}] mode:destroy flags[Prop2] mappers[mateState],
            item 1 [MateArgentino.Termo] mode:keep flags[NotEmpty;Prop1],
            -fluid 0.045 [HotWater],
        }}
        outputs
        {{
            item 1 mapper:mateState,
        }}
        itemMapper mateState
        {{
{hot_pour_map}
        }}
    }}

    craftRecipe VaciarMate
    {{
        timedAction = Making,
        time = 20,
        AllowBatchCraft = false,
        Tags = InHandCraft;Cooking;CanBeDoneInDark,
        category = Cooking,
        inputs
        {{
            item 1 [MateArgentino.MateLavado] mode:destroy flags[Prop1],
        }}
        outputs
        {{
            item 1 MateArgentino.MateVacio,
        }}
    }}
}}
"""


def make_fluids() -> str:
    return """module MateArgentino
{
    fluid HotWater
    {
        ColorReference = LightSkyBlue,
        DisplayName = Fluid_Name_MateArgentino_HotWater,
        Categories
        {
            Beverage,
            Water,
        }
        Properties
        {
            ThirstChange = -50.0,
        }
    }

    fluid MateInfusion
    {
        ColorReference = PaleGreen,
        DisplayName = Fluid_Name_MateArgentino_MateInfusion,
        Categories
        {
            Beverage,
        }
        Properties
        {
            ThirstChange = -333.333,
            UnhappyChange = -133.333,
            Calories = 66.667,
        }
    }

    fluid MateInfusionHot
    {
        ColorReference = PaleGreen,
        DisplayName = Fluid_Name_MateArgentino_MateInfusionHot,
        Categories
        {
            Beverage,
        }
        Properties
        {
            ThirstChange = -333.333,
            fatigueChange = -177.778,
            UnhappyChange = -133.333,
            Calories = 66.667,
        }
    }
}
"""


def write_translations(language: str) -> None:
    is_es = language == "ES"
    item_names = {
        "MateArgentino.MateVacio": "Mate vacío" if is_es else "Empty mate",
        "MateArgentino.MateLavado": "Mate lavado" if is_es else "Washed-out mate",
        "MateArgentino.Termo": "Termo" if is_es else "Thermos",
    }
    for item_id, quality, _count in yerba_ids():
        item_names[f"MateArgentino.{item_id}"] = QUALITIES[quality][
            "es" if is_es else "en"
        ]
    for count in range(1, MAX_CEBADAS + 1):
        item_names[f"MateArgentino.MateConYerba{count}"] = (
            "Mate con yerba" if is_es else "Mate with yerba"
        )
        item_names[f"MateArgentino.MatePreparado{count}"] = (
            "Mate preparado" if is_es else "Prepared mate"
        )
        item_names[f"MateArgentino.MatePreparadoCaliente{count}"] = (
            "Mate caliente" if is_es else "Hot mate"
        )

    tooltips = {
        "Tooltip_MateArgentino_YerbaEconomica": (
            "Rinde entre 10 y 15 cebadas." if is_es else "Lasts for 10 to 15 infusions."
        ),
        "Tooltip_MateArgentino_YerbaMedia": (
            "Rinde entre 15 y 25 cebadas." if is_es else "Lasts for 15 to 25 infusions."
        ),
        "Tooltip_MateArgentino_YerbaPremium": (
            "Rinde entre 25 y 40 cebadas." if is_es else "Lasts for 25 to 40 infusions."
        ),
        "Tooltip_MateArgentino_MateVacio": (
            "Cargalo con un paquete de yerba."
            if is_es
            else "Load it with a package of yerba."
        ),
        "Tooltip_MateArgentino_MateLavado": (
            "La yerba está lavada. Vaciá el mate para volver a usarlo."
            if is_es
            else "The yerba is washed out. Empty the mate before reusing it."
        ),
        "Tooltip_MateArgentino_Termo": (
            "Capacidad: 1 litro. Mantiene el agua caliente durante 24 horas. Cada cebada usa 45 ml."
            if is_es
            else "Capacity: 1 litre. Keeps water hot for 24 hours. Each infusion uses 45 ml."
        ),
    }
    for count in range(1, MAX_CEBADAS + 1):
        tooltips[f"Tooltip_MateArgentino_Restantes{count}"] = (
            f"Quedan {count} cebada{'s' if count != 1 else ''}."
            if is_es
            else f"{count} infusion{'s' if count != 1 else ''} remaining."
        )
        remaining = count - 1
        es_remaining = (
            "Después queda 1."
            if remaining == 1
            else f"Después quedan {remaining}."
        )
        en_remaining = (
            "1 remains afterwards."
            if remaining == 1
            else f"{remaining} remain afterwards."
        )
        tooltips[f"Tooltip_MateArgentino_Preparado{count}"] = (
            (
                f"45 ml de infusión listos para beber. {es_remaining}"
                if remaining
                else "Última cebada. Después queda lavado."
            )
            if is_es
            else (
                f"45 ml of mate infusion ready to drink. {en_remaining}"
                if remaining
                else "Last infusion. It will be washed out afterwards."
            )
        )
        tooltips[f"Tooltip_MateArgentino_PreparadoCaliente{count}"] = (
            (
                f"45 ml de mate caliente: reduce el cansancio. {es_remaining}"
                if remaining
                else "Última cebada caliente: reduce el cansancio. Después queda lavado."
            )
            if is_es
            else (
                f"45 ml of hot mate: reduces fatigue. {en_remaining}"
                if remaining
                else "Last hot infusion: reduces fatigue. It will be washed out afterwards."
            )
        )

    language_dir = TRANSLATE / language
    (language_dir / "ItemName.json").write_text(
        json.dumps(item_names, ensure_ascii=False, indent=4) + "\n",
        encoding="utf-8",
    )
    (language_dir / "Tooltip.json").write_text(
        json.dumps(tooltips, ensure_ascii=False, indent=4) + "\n",
        encoding="utf-8",
    )
    fluids = {
        "Fluid_Container_Termo": "Termo" if is_es else "Thermos",
        "Fluid_Container_Mate": "Mate",
        "Fluid_Name_MateArgentino_HotWater": (
            "Agua caliente" if is_es else "Hot water"
        ),
        "Fluid_Name_MateArgentino_MateInfusion": (
            "Infusión de mate" if is_es else "Mate infusion"
        ),
        "Fluid_Name_MateArgentino_MateInfusionHot": (
            "Infusión de mate caliente" if is_es else "Hot mate infusion"
        ),
    }
    recipes = {
        "CargarYerbaMate": (
            "Poner yerba en el mate" if is_es else "Fill Mate with Yerba"
        ),
        "CebarMate": "Cebar mate" if is_es else "Pour Mate",
        "CebarMateCaliente": (
            "Cebar mate con agua caliente"
            if is_es
            else "Pour Mate with Hot Water"
        ),
        "VaciarMate": "Vaciar mate" if is_es else "Empty Mate",
    }
    (language_dir / "Fluids.json").write_text(
        json.dumps(fluids, ensure_ascii=False, indent=4) + "\n",
        encoding="utf-8",
    )
    (language_dir / "Recipes.json").write_text(
        json.dumps(recipes, ensure_ascii=False, indent=4) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    (SCRIPTS / "MateArgentino_Items.txt").write_text(
        make_items(), encoding="utf-8"
    )
    (SCRIPTS / "MateArgentino_Recipes.txt").write_text(
        make_recipes(), encoding="utf-8"
    )
    (SCRIPTS / "MateArgentino_Fluids.txt").write_text(
        make_fluids(), encoding="utf-8"
    )
    write_translations("ES")
    write_translations("EN")
    print("Generated 3 yerba qualities and 40 persistent mate states.")


if __name__ == "__main__":
    main()
