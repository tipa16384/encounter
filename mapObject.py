class Weapon():
    def __init__(self, name: str, damage: int, range: int, is_blessed=False, can_be_tempered=False, is_tempered=False, can_be_blessed=False):
        self.name = name
        self.damage = damage
        self.range = range
        self.is_blessed = is_blessed
        self.can_be_tempered = can_be_tempered
        self.is_tempered = is_tempered
        self.can_be_blessed = can_be_blessed

    def __str__(self):
        return f"{self.name}"
    
    def __repr__(self):
        return f"{self.name}"
    
    # getters
    def get_name(self) -> str:
        return self.name
    
    def get_damage(self) -> int:
        return self.damage
    
    def get_range(self) -> int:
        return self.range
    
    def get_is_blessed(self) -> bool:
        return self.is_blessed

    def get_can_be_tempered(self) -> bool:
        return self.can_be_tempered

    def get_is_tempered(self) -> bool:
        return self.is_tempered
    
    def get_can_be_blessed(self) -> bool:
        return self.can_be_blessed

class Shield():
    def __init__(self, name: str, defense: int, durability: int):
        self.name = name
        self.defense = defense
        self.durability = durability

    def __str__(self):
        return f"{self.name}"
    
    def __repr__(self):
        return f"{self.name}"
    
    # getters
    def get_name(self) -> str:
        return self.name
    
    def get_defense(self) -> int:
        return self.defense
    
    def get_durability(self) -> int:
        return self.durability

PLAYER_SYMBOL = '@'
DRAGON_SYMBOL = 'D'    

def getWeapons():
    weapons = []
    weapons.append(Weapon('your bare hands', 0, 1))
    weapons.append(Weapon('a melted sword', 1, 1))
    weapons.append(Weapon('an untempered sword', 2, 1, can_be_tempered=True))
    weapons.append(Weapon('a tempered sword', 5, 1, is_tempered=True, can_be_blessed=True))
    weapons.append(Weapon('Excalibur', 100, 1, is_blessed=True, is_tempered=True))
    weapons.append(Weapon('dragon teeth', 2, 1, can_be_blessed=True, is_tempered=True))
    weapons.append(Weapon('adamantine teeth', 2, 1, is_blessed=True, is_tempered=True))
    return weapons

def getShields():
    shields = []
    shields.append(Shield('no shield', 0, 0))
    shields.append(Shield('a piece of wooden wall', 2, 60))
    shields.append(Shield('a wooden shield', 2, 50))
    shields.append(Shield('a bolstered wooden shield', 3, 20))
    shields.append(Shield('a wooden kite shield', 5, 10))
    return shields

class MapObject():
    def __init__(self, name: str, symbol: str, blocks=False, destructible=False, wet=False, mobile=False, openable=False,
                 move_timer=0, move_cooldown=0, shield=0, is_ore=False, starting_weapon=0, is_wood=False,
                 breath_timer=0, breath_cooldown=0, breath_range=0, max_health=0):
        self.name = name
        self.blocks = blocks
        self.destructible = destructible
        self.symbol = symbol
        self.mobile = mobile
        self.wet = wet
        self.openable = openable
        self.is_wet = False
        self.is_burning = False
        self.is_blessed = False
        self.move_timer = move_timer
        self.move_cooldown = move_cooldown
        self.shield = shield
        self.carrying_ore = False
        self.is_ore = is_ore
        self.weapon = starting_weapon
        self.is_wood = is_wood
        self.breath_timer = breath_timer
        self.breath_cooldown = breath_cooldown
        self.breath_range = breath_range
        self.max_health = max_health
        self.health = max_health

    def __str__(self):
        return f"{self.name} {self.symbol} {self.blocks} {self.destructible}"
    
    def __repr__(self):
        return f"{self.name} {self.symbol} {self.blocks} {self.destructible}"

    # getters
    def get_name(self) -> str:
        return self.name
    
    def get_symbol(self) -> str:
        return self.symbol
    
    def get_blocks(self) -> bool:
        return self.blocks
    
    def get_destructible(self) -> bool:
        return self.destructible
    
    def get_mobile(self) -> bool:
        return self.mobile

    def get_wet(self) -> bool:
        return self.wet
    
    def get_openable(self) -> bool:
        return self.openable
    
    def get_is_wet(self) -> bool:
        return self.is_wet
    
    def set_is_wet(self, is_wet: bool):
        self.is_wet = is_wet
    
    def get_is_burning(self) -> bool:
        return self.is_burning
    
    def set_is_burning(self, is_burning: bool):
        self.is_burning = is_burning
    
    def get_is_blessed(self) -> bool:
        return self.is_blessed
    
    def set_is_blessed(self, is_blessed: bool):
        self.is_blessed = is_blessed
    
    def get_move_timer(self) -> int:
        return self.move_timer
    
    def get_move_cooldown(self) -> int:
        return self.move_cooldown
    
    def set_move_cooldown(self, move_cooldown: int):
        self.move_cooldown = move_cooldown

    def get_has_shield(self) -> bool:
        return self.shield > 0
    
    def get_shield(self) -> int:
        return self.shield
    
    def set_shield(self, shield_index: int):
        self.shield = max(0, shield_index)
    
    def get_carrying_ore(self) -> bool:
        return self.carrying_ore
    
    def set_carrying_ore(self, carrying_ore: bool):
        self.carrying_ore = carrying_ore
        
    def get_is_ore(self) -> bool:
        return self.is_ore
    
    def get_weapon(self) -> int:
        return self.weapon
    
    def set_weapon(self, weapon_index: int):
        self.weapon = weapon_index
    
    def get_is_wood(self) -> bool:
        return self.is_wood

    def get_breath_timer(self) -> int:
        return self.breath_timer
    
    def get_breath_cooldown(self) -> int:
        return self.breath_cooldown
    
    def set_breath_cooldown(self, breath_cooldown: int):
        self.breath_cooldown = breath_cooldown
    
    def get_breath_range(self) -> int:
        return self.breath_range
    
    def get_max_health(self) -> int:
        return self.max_health
    
    def get_health(self) -> int:
        return self.health
    
    def set_health(self, health: int):
        self.health = max(0, health)
    
def getMapObjects():
    map_objects = {}
    map_objects['#'] = MapObject('stone wall', '#', blocks=True)
    map_objects['-'] = MapObject('wooden wall', '-', blocks=True, destructible=True, is_wood=True)
    map_objects['+'] = MapObject('door', '+', blocks=True, destructible=True, openable=True)
    map_objects['@'] = MapObject('player', PLAYER_SYMBOL, blocks=True, mobile=True, move_timer=1, starting_weapon=2, max_health=10)
    map_objects['D'] = MapObject('dragon', DRAGON_SYMBOL, blocks=True, mobile=True, move_timer=2, breath_timer=5, breath_range=3, max_health=100, starting_weapon=5)
    map_objects['~'] = MapObject('water', '~', wet=True)
    map_objects['%'] = MapObject('holy ore', '%', blocks=True, destructible=True, is_ore=True)
    map_objects['*'] = MapObject('altar', '*', blocks=True)
    return map_objects