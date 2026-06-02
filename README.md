# Tank-Attack

Juego de tanques tipo arcade que combina **Programación Orientada a Objetos** (Python + Pygame) con el **paradigma lógico** (SWI-Prolog vía PySwip) para la inteligencia artificial de los enemigos.

Proyecto 2 — Lenguajes de Programación · 2026 · Instituto Tecnológico de Costa Rica, Sede San Carlos.

---

## Requisitos del sistema

- **Python 3.9** o superior
- **SWI-Prolog 8** o superior (probado con 10.0.2)
- **pip** para instalar las dependencias Python

### macOS

```bash
brew install swi-prolog
```

### Linux (Debian / Ubuntu)

```bash
sudo apt-get install swi-prolog
```

### Windows

Descargar el instalador desde <https://www.swi-prolog.org/download/stable> y agregar `swipl` al `PATH`.

---

## Instalación

```bash
# 1. Clonar
git clone https://github.com/KARG2606/Tank-attack.git
cd Tank-attack

# 2. Entorno virtual e instalación de dependencias
python3 -m venv venv
source venv/bin/activate          # en Windows: venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt

# 3. Verificar que el puente Python ↔ Prolog está vivo
python3 -c "from pyswip import Prolog; p=Prolog(); print(list(p.query('member(X,[1,2,3])')))"
```

Si el último comando imprime `[{'X': 1}, {'X': 2}, {'X': 3}]`, todo bien.

---

## Ejecución

```bash
source venv/bin/activate
python3 main.py
```

Para reproducir un nivel exactamente igual (útil para depurar):

```bash
TANK_SEED=42 python3 main.py
```

---

## Controles

| Tecla | Acción |
|---|---|
| `W` `A` `S` `D` o flechas | Mover el tanque del jugador |
| `Espacio` | Disparar |
| `R` | Reiniciar el nivel actual |
| `Enter` / `Espacio` / clic | Iniciar partida desde el menú o avanzar de nivel |
| `Esc` | Cerrar el juego |

**Cómo se juega.** Destruí los **objetivos** (cuadrados amarillos y rosas) de cada nivel antes de quedarte sin las **3 vidas**. Los tanques enemigos custodian sus objetivos y atacarán cuando te acerques.

| Halo | Tanque |
|---|---|
| 🟢 verde brillante | Jugador |
| 🔴 rojo | ASSAULT (ágil, alerta a corta distancia) |
| 🔵 azul | DEFENDER (custodia objetivo) |
| 🟣 morado | FLANKER (embosca usando coordinación táctica) |

---

## Editor de pantallas

Edita un mapa existente o crea uno nuevo desde cero:

```bash
# Editar uno existente
python3 -m ui.editor_pantallas maps/level1.txt

# Crear uno en blanco
python3 -m ui.editor_pantallas
```

**Controles del editor**

| Acción | Cómo |
|---|---|
| Cambiar contenido de una celda | clic izquierdo (cicla `. → # → P → O → Q → 1 → 2 → 3`) |
| Vaciar una celda | clic derecho |
| Guardar (con validación) | `S` |
| Recargar desde disco | `R` |
| Validar y mostrar errores | `V` |
| Salir | `Esc` |

El editor avisa si:
- las filas no tienen el mismo ancho,
- hay caracteres inválidos,
- el jugador (`P`) está ausente o duplicado,
- el mapa no tiene objetivos,
- existen celdas no muro **aisladas** de la posición del jugador (BFS).

---

## Estructura del proyecto

```
Tank-attack/
├── main.py                       # punto de entrada
├── requirements.txt              # pygame, pyswip
├── ai/
│   └── enemy_state.py            # Enum con 7 estados de la FSM enemiga
├── entities/
│   ├── entity.py                 # base abstracta
│   ├── wall.py
│   ├── objective.py              # ObjetivoTipo1, ObjetivoTipo2
│   ├── player_tank.py            # vidas, disparo, invulnerabilidad
│   ├── enemy_tank.py             # roles, FSM, lógica táctica
│   └── bullet.py
├── game/
│   ├── constants.py
│   ├── collision_manager.py
│   ├── level_loader.py
│   ├── assets.py                 # carga sprites + rotación por dirección
│   └── game_manager.py           # loop principal, menú, multi-nivel, HUD
├── logic/
│   ├── ai_controller.py          # capa de alto nivel
│   ├── pathfinding.py            # BFS en Python como fallback
│   ├── prolog_bridge.py          # adaptador delgado al PrologManager
│   └── tactical_manager.py       # coordinación táctica (Fase 7 extra)
├── prolog/
│   ├── prolog_manager.py         # puente PySwip ↔ SWI-Prolog
│   ├── pathfinding.pl            # DFS con heurística Manhattan
│   └── decision.pl               # decidir_accion, cerca_de_jugador, ...
├── util/
│   └── generador_aleatorio.py    # randomización con BFS de alcanzabilidad
├── ui/
│   └── editor_pantallas.py       # editor visual de mapas
├── maps/
│   ├── level1.txt
│   ├── level2.txt
│   └── level3.txt
└── resourses/                    # sprites (jugador, enemigos, muro, objetivo, fondo)
```

---

## Resolución de problemas

### `ModuleNotFoundError: No module named 'pyswip'`

Activa el entorno virtual:

```bash
source venv/bin/activate
pip install -r requirements.txt
```

### `Could not find/open foreign resource libswipl`

En macOS PySwip a veces no encuentra el `libswipl` de SWI-Prolog. Exporta:

```bash
export SWI_HOME_DIR="/opt/homebrew/lib/swipl"
export DYLD_FALLBACK_LIBRARY_PATH="/opt/homebrew/lib"
```

(O las rutas equivalentes según donde tengas instalado SWI-Prolog: `which swipl` y subir desde ahí).

### El juego se ve muy lento

Bajá el FPS objetivo en [`game/constants.py`](game/constants.py) o reducí el intervalo de consulta a Prolog (`_prolog_query_interval` en [`game/game_manager.py`](game/game_manager.py)).

### Quiero reproducir exactamente la misma partida

```bash
TANK_SEED=<entero> python3 main.py
```

La semilla fija las posiciones aleatorias de objetivos y enemigos.

---

## Documentación adicional

- [`docs/informe.md`](docs/informe.md) — informe técnico completo (arquitectura, predicados Prolog, heurística DFS, manuales, conclusiones).
- Guía de diseño original — `Guia_TankAttack.pdf` (incluida en la entrega).
- Enunciado oficial — `Tarea2 (Lógico y OO).pdf`.

---

## Créditos

- **NOMBRE_AQUÍ** — desarrollo OO, gameplay, UI, niveles, editor, integración.
- **NOMBRE_AQUÍ** — predicados Prolog, motor de decisiones, coordinación táctica.
- Profesor: Oscar Víquez Acuña.
