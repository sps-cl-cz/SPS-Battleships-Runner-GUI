# SPS-Battleships-Runner-GUI

## Hlavní změny oproti původní verzi
1. **Grafické rozhraní** - Přidána vizualizace herních ploch pomocí matplotlib
2. **Logování** - Každý tah je nyní zaznamenáván do log souborů
3. **Snímky stavu** - Ukládání obrázků herních ploch po každém tahu ve složce [logs](./logs/)
4. **Interaktivní režim** - Herní plochy se aktualizují v reálném čase
5. **Vylepšené barevné schéma** - Rozlišení různých stavů buněk (prázdné, loď, zásah, potopení, mino)
6. **Jednodušší spuštění** - Výchozí počet her nastaven na 1 pro lepší vizualizaci

## Jak hra funguje

### Herní mechanika
1. Každý hráč má svou herní plochu (10x10 buněk)
2. Hráči střídavě útočí na soupeřovu plochu
3. Útok je specifikován souřadnicemi (x,y)
4. Výsledek útoku může být:
   - **Minul** - Cílová buňka je prázdná
   - **Zásah** - Cílová buňka obsahuje část lodi
   - **Potopení** - Byl zasažen poslední segment lodi

### Reprezentace herní plochy
- **0**: Prázdná voda
- **1-7**: ID lodi
- **8**: Zásah
- **9**: Potopení
- **10**: Minul

## Typy lodí
| ID | Name | Size | Shape |
|----|------|------|-------|
| 1  | Destroyer | 2 | I |
| 2  | Cruiser | 3 | I |
| 3  | Battleship | 4 | I |
| 4  | Aircraft Carrier | 4 | T |
| 5  | Submarine | 4 | L |
| 6  | Cruiser II | 4 | Z |
| 7  | Super Ship | 6 | TT |

### Grafické znázornění lodí
![Grafické zobrazení lodí](/examples/Images/ships.png)

### Správný a špatný placement
![Správné a nesprávné umístění lodí](/examples/Images/placement.png)

### Konec hry
Hra končí, když jeden z hráčů zničí všechny soupeřovy lodě.

## Jak sestavit robota

### 1. Struktura projektu
```
player_X/
├── board_setup/
│   └── board_setup.py  # Obsahuje třídu BoardSetup
├── strategy/
│   └── strategy.py     # Obsahuje třídu Strategy
└── tests/              # Obsahuje testy co musí soubory výše splňovat
```

### 2. BoardSetup třída
Musí implementovat:
```python
class BoardSetup:
    def __init__(self, height: int, width: int, ships: dict):
        # Inicializace
        pass
        
    def place_ships(self):
        # Umístění lodí na plochu
        pass
        
    def get_board(self) -> list[list[int]]:
        # Vrátí herní plochu
        return board
```

### 3. Strategy třída
Musí implementovat:
```python
class Strategy:
    def __init__(self, height: int, width: int, ships: dict):
        # Inicializace
        pass
        
    def get_next_attack(self) -> tuple[int, int]:
        # Vrátí souřadnice dalšího útoku
        return x, y
        
    def register_attack(self, x: int, y: int, is_hit: bool, is_sunk: bool):
        # Zaznamená výsledek útoku
        pass
```

### 4. Doporučené strategie
- **Probability Density** - Útok na buňky s nejvyšší pravděpodobností výskytu lodi
- **Hunt/Target** - Kombinace náhodného hledání a cíleného útoku
- **Parity** - Útok pouze na buňky určité parity
- **Shape Detection** - Identifikace tvarů lodí podle zásahů

### 5. Testování
- Spusťte `python battle.py -v` pro podrobný výpis
- Pro vizualizaci použijte `python battle.py` (výchozí 1 hra)
- Pro více her použijte `python battle.py -c X` (X = počet her)

# Upozornění
 - Vykreslování GUI je HW náročné a proto se nedoporučuje pouštět více jak jednu hru 
