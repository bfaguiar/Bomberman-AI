from enum import IntEnum

class Powerups(IntEnum):
    Bombs = 1,
    Flames = 2,     
    Speed = 3,      # aumenta a velocidade do bm
    Wallpass = 4,   # atravessa paredes destrutiveis
    Detonator = 5,  # tem detonador "A"
    Bombpass = 6,   # atravessa bombas
    Flamepass = 7,  # atravessa o hit da bomba ?
    Mystery = 8  

class Speed(IntEnum):
    SLOWEST = 1,
    SLOW = 2,
    NORMAL = 3,
    FAST = 4

class Smart(IntEnum):
    LOW = 1,
    NORMAL = 2,
    HIGH = 3