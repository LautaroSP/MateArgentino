# YerbaMate — Project Zomboid Build 42

Agrega un mate reutilizable, un termo de un litro y paquetes de yerba.

## Ciclo de uso

1. Combina `Mate vacío` con un paquete de yerba económica, media o premium.
2. Llena el termo y, si querés el bonus, calentá el agua en una cocina, horno
   o fogata.
3. Usa `Cebar mate` con agua normal o `Cebar mate con agua caliente`; cada
   cebada consume 0,045 L.
4. Usa el menú nativo `Beber` para tomar todo, la mitad o un cuarto.
5. Repite el cebado hasta lavar la yerba.
6. Usa `Vaciar mate` para recuperar el mate vacío.

El rendimiento se sortea cuando aparece cada paquete:

- Económica (color original): 10 a 15 cebadas.
- Media (amarilla): 15 a 25 cebadas.
- Premium (verde): 25 a 40 cebadas.

Los 40 estados posibles son objetos internos, por lo que el contador persiste
al guardar la partida y no depende de lógica exclusiva del cliente. Los
objetos de versiones anteriores siguen siendo compatibles.

Cada cebada usa 45 ml: un termo lleno de un litro rinde unas 22 cebadas. El mate
cebado es un recipiente de líquido real y usa las opciones nativas para beber
todo, la mitad o un cuarto. Cuando queda vacío vuelve automáticamente al estado
de mate con yerba y descuenta una cebada.

El termo utiliza la temperatura nativa de Build 42 para detectar cuándo el agua
se calentó. Desde ese momento conserva el estado caliente durante 24 horas de
juego. El mate preparado con agua caliente reduce el cansancio; el preparado
con agua normal no tiene ese bonus.

Mientras el personaje bebe se reproduce en loop el sonido
`media/sound/MateArgentino_RuidoMate.mp3`. El juego lo detiene al completar o
cancelar la acción.

## Instalación local

Copia la carpeta `MateArgentino` completa dentro de:

`C:\Users\<usuario>\Zomboid\Workshop\`

Luego abre el juego, entra en `Mods` y activa `YerbaMate`.

## Prueba rápida

Inicia el juego con `-debug`, abre `General Debuggers > Items List` y busca:

- `MateArgentino.MateVacio`
- `MateArgentino.YerbaEconomica`
- `MateArgentino.YerbaMedia`
- `MateArgentino.YerbaPremium`
- `MateArgentino.Termo`

## Estado actual

- Diseñado para Build 42.20.
- Incluye traducciones ES/EN.
- Incluye distribución de botín.
- Al dejarlos en el suelo usa modelos 3D propios: mate con bombilla y estados
  visuales, termo metálico y paquetes de yerba económica, media y premium.
- Las escalas compensan la conversión de unidades de Blender a Project
  Zomboid. El mate queda ligeramente más grande que una taza vanilla.
- El termo muestra sus estados vacío, con agua y con agua caliente mediante el
  sistema de fluidos de Build 42.
- Al cebar y beber se utiliza el modelo 3D del mate como objeto en la mano,
  manteniendo provisionalmente las animaciones nativas de preparar y beber.
- La animación corporal específica del mate queda para una fase posterior.
