# MateArgentino - Animación del mate con Paddlefruit Community Rig (GLB)

> Estado B42.20: el GLB quedó deshabilitado porque exportaba el esqueleto
> completo y el nodo incompatible `Body`. El juego utiliza actualmente
> `anims_X/Bob/Bob_MateSip.x`, generado por
> `tools/export_mate_sip_left.py`: brazo izquierdo + `Bip01_Prop2`, sin
> canales del brazo derecho ni del tren inferior.

El mod usa el **Paddlefruit Community Rig v4.0.1** para editar la animación
`Bob_MateSip` visualmente en Blender y exportarla como GLB (el formato que el
juego carga vía Assimp/jassimp desde `anims_X/Bob/`).

## Archivos

| Archivo | Rol |
|---|---|
| `PZ_HumanRigV4.blend` | Rig original descargado (no modificar). |
| `MateSip_rig.blend` | **Archivo de trabajo**: rig + action `Bob_MateSip` ya remapeada en los huesos CTRL (frames 0-124, 30fps). Abrir este para editar. |
| `Bob_MateSip.glb` | GLB exportado (ya copiado al mod y al workshop). |
| `Bob_MateSip.x` | Respaldo `.x` de la animación (legacy, no se usa con el GLB activo). |
| `rig_fix.py` | Parche para el remap del rig v4.0.1 (solo para re-importar `.x`). |

Destinos del GLB:
- Mod: `Contents/mods/MateArgentino/42/media/anims_X/Bob/Bob_MateSip.glb`
- Workshop: `C:\Users\lauta\Zomboid\Workshop\MateArgentino\Contents\mods\MateArgentino\42\media\anims_X\Bob\Bob_MateSip.glb`

El XML `AnimSets/player/actions/MateSip.xml` (nodo `DrinkMate`) no cambia: sigue
referenciando la animación por nombre `Bob_MateSip`.

## Editar la animación en Blender (GUI)

1. Abre `MateSip_rig.blend` en Blender 5.2.
2. Si Blender pregunta por el script `PY-PZ_HumanRig.py` (deshabilitado para el
   archivo), acéptalo para ejecutarlo. Si no pregunta, ábrelo en el editor de
   texto y pulsa "Run Script".
3. Selecciona el rig `OBJ-HumanRig (0)`. La action `Bob_MateSip` ya está puesta.
4. En **Pose Mode**, recorre los frames 0-124. Los huesos a mover para el sorbo:
   - `CTRL-Spine2` (torso), `CTRL-Chest` (cuello), `CTRL-Head` (cabeza)
   - Brazo derecho: `CTRL-Shoulder.R`, `CTRL-UpperArmFK.R`,
     `CTRL-ForearmFK.R`, `CTRL-HandFK.R`
   - Mate en mano: `CTRL-Prop.L` (el mate va en `Bip01_Prop2`)
5. Ajusta la pose y mete keyframes (botón derecho / `I` en el hueso) como en
   cualquier animación FK. La animación actual es base -> sorbo -> base
   (frames 0, ~60, 124).

### Exportar el GLB

1. Con el rig seleccionado, abre el panel **N** (barra lateral) > pestaña
   **Item** > **Zomboid Human Rig Properties** > subpanel **Export**.
2. En **Output Directory** pon la carpeta donde quieras el GLB (p. ej. la de
   `anims_X\Bob` del mod).
3. Deja **Batch Export** desmarcado (exporta solo la action activa) o, si está
   marcado, asegúrate de que el **Action Filter** contenga `Bob_MateSip`.
4. Pulsa **Export GLBs for Project Zomboid**. Genera `<action>.glb`
   (en nuestro caso `Bob_MateSip.glb`).
5. Copia `Bob_MateSip.glb` al mod y al workshop (rutas de arriba).
   **Importante:** si existe `Bob_MateSip.x` junto al GLB, el juego podría cargar
   uno u otro; para probar el GLB deja solo el GLB.
6. Arranca Project Zomboid con el mod, toma mate y verifica el movimiento.

## Re-importar una animación `.x` (opcional)

El remap del rig v4.0.1 trae dos bugs (falta la propiedad `imported_animation_active_index`
y el `control_dict` apunta a `CTRL-Hand.L/.R` que no existen; son `CTRL-HandFK.L/.R`).
Para re-importar un `.x` en la GUI:

1. En el editor de texto de Blender abre `rig_fix.py` y pulsa "Run Script".
2. Sigue las instrucciones que imprime (Python console) para apuntar a un `.x`
   y llamar `bpy.ops.zomboid.remap_animation()`.

## Pipeline headless (reproducir la exportación)

`Bob_MateSip.glb` se generó así (todo en Blender headless):

1. `bpy.ops.import_scene.directx_x(filepath=Bob_MateSip.x)` (addon `io_directx_x`).
2. Ejecutar `PY-PZ_HumanRig.py` + `register()`, parchear las dos propiedades
   (igual que `rig_fix.py`).
3. `bpy.ops.zomboid.remap_animation()` con `pz_human_imported_animations[0]`
   apuntando a `Bob_MateSip.x`. Crea la action `Bob_MateSip (IMPORT)` en los
   huesos CTRL (10 huesos: Spine, Spine1, Neck, Head, R_Clavicle, R_UpperArm,
   R_Forearm, R_Hand, R_Finger0/1, Prop2).
4. Renombrar la action a `Bob_MateSip`, ponerla como activa del rig.
5. `p.file_output_path = <anims_X/Bob>`, `p.batch_export = False`,
   `bpy.ops.zomboid.export_glb()`.
