from mapObject import getMapObjects, getWeapons, getShields, PLAYER_SYMBOL, DRAGON_SYMBOL
import curses
import random
import heapq

map_file = 'map.txt'

BASH_CHANCE = 0.25
BURN_CHANCE = 0.5
ORTHOGONALS = [(-1, 0), (1, 0), (0, -1), (0, 1)]
DXY_TO_COMMAND = {(-1, 0): 'h', (1, 0): 'l', (0, -1): 'k', (0, 1): 'j', (0,0): '.'}

def load_map(map_file: str) -> list:
    # read the map file. return a list of tuples of the form (x, y, MapObject).
    # ignore any symbols that are not in the map_objects dictionary.
    map_objects = getMapObjects()
    map_data = []
    with open(map_file) as f:
        for y, line in enumerate(f):
            for x, symbol in enumerate(line.rstrip()):
                if symbol in map_objects:
                    map_data.append((x, y, map_objects[symbol]))
    return map_data

def get_other_mob(map_data: list, symbol: str) -> tuple:
    # return the tuple (x, y, MapObject) of the other mobile object in map_data.
    for motuple in map_data:
        _, _, map_object = motuple
        if map_object.get_mobile() and map_object.get_symbol() != symbol:
            return motuple

    raise ValueError("No other mobile object found")

def distance(start: tuple, end: tuple) -> int:
    # return the Manhattan distance between the two points.
    return abs(start[0] - end[0]) + abs(start[1] - end[1])

def display_map(stdscr, map_data: list):
    # display non-destructible objects
    for x, y, map_object in map_data:
        if not map_object.get_destructible():
            stdscr.addch(y, x, map_object.get_symbol())
    # display destructible but non-mobile objects
    for x, y, map_object in map_data:
        if map_object.get_destructible() and not map_object.get_mobile():
            stdscr.addch(y, x, map_object.get_symbol())
    # display mobile objects
    for x, y, map_object in map_data:
        if map_object.get_mobile():
            stdscr.addch(y, x, map_object.get_symbol())

def extract_map_object(map_data: list, symbol: str) -> tuple:
    map_objects = getMapObjects()
    # extract the map object with the given symbol from map_data. return the tuple (x, y, MapObject).
    for motuple in map_data:
        _, _, map_object = motuple
        if map_object.get_symbol() == symbol:
            return motuple
    
    # if the symbol is not found, log it, using map_objects to get the name of the object
    if symbol in map_objects:
        errors = f"{map_objects[symbol].get_name()} not found in map data"
    else:
        errors = f"Symbol {symbol} not found in map objects"
    
    raise ValueError(errors)

def move_map_object(map_data: list, symbol: str, x: int, y: int) -> list:
    # move the map object with the given symbol to the new position (x, y). return the updated map_data.
    new_map_data = []
    for motuple in map_data:
        _, _, map_object = motuple
        if map_object.get_symbol() == symbol:
            new_map_data.append((x, y, map_object))
        else:
            new_map_data.append(motuple)
    return new_map_data

def move_mob(map_data: list, symbol: str, dx: int, dy: int) -> list:
    # move the mobile map object with the given symbol by the offset (dx, dy). return the updated map_data.
    motuple = extract_map_object(map_data, symbol)
    x, y, map_object = motuple
    new_x = x + dx
    new_y = y + dy
    map_object.set_move_cooldown(map_object.get_move_timer())
    # if there is water at the new spot, set the object to be wet
    for mx, my, nmo in map_data:
        if nmo.get_wet() and mx == new_x and my == new_y:
            if map_object.get_is_burning():
                log(symbol, "You douse the flames on your clothes.", "Dragons don't catch fire")
                map_object.set_is_burning(False)
                map_object.set_is_wet(True)
            elif not map_object.get_is_wet():
                log(symbol, "You splash around in the water.", "The dragon splashes around in the water.")
                map_object.set_is_wet(True)
    return move_map_object(map_data, symbol, new_x, new_y)

def set_quit(map_data: list):
    global global_quit
    global_quit = True
    return map_data

def direction_blocked(map_data: list, symbol: str, dx: int, dy: int) -> bool:
    # check if the direction (dx, dy) is blocked by a wall or another object. return True if blocked, False otherwise.
    x, y, map_object = extract_map_object(map_data, symbol)

    if map_object.get_move_cooldown() > 0:
        return True

    new_x = x + dx
    new_y = y + dy
    for mx, my, map_object in map_data:
        if map_object.get_blocks() and mx == new_x and my == new_y:
            return True
    return False

def can_open_door(map_data: list, symbol: str) -> bool:
    # return True if the '+' symbol is in one of the four cardinal directions of the player, False otherwise.
    x, y, _ = extract_map_object(map_data, symbol)
    for dx, dy in ORTHOGONALS:
        new_x = x + dx
        new_y = y + dy
        for mx, my, map_object in map_data:
            if map_object.get_openable() and mx == new_x and my == new_y:
                return True
    return False

def open_door(map_data: list, symbol: str) -> list:
    # if the '+' symbol is in one of the four cardinal directions of the player, replace it with a '-' symbol. return the updated map_data.
    x, y, _ = extract_map_object(map_data, symbol)
    for dx, dy in ORTHOGONALS:
        new_x = x + dx
        new_y = y + dy
        for motuple in map_data:
            mx, my, map_object = motuple
            if map_object.get_openable() and mx == new_x and my == new_y:
                # remove the door
                del map_data[map_data.index(motuple)]
                log(symbol, "You open the door. It falls to the ground with a loud crash.", "The dragon tears the door off its hinges.")

    return map_data

def can_attack(map_data: list, symbol: str) -> bool:
    # return True if a mobile object is in one of the four cardinal directions of the player, False otherwise.
    x, y, _ = extract_map_object(map_data, symbol)
    for dx, dy in ORTHOGONALS:
        new_x = x + dx
        new_y = y + dy
        for mx, my, map_object in map_data:
            if map_object.get_mobile() and mx == new_x and my == new_y:
                return True
    return False

def attack(map_data: list, symbol: str) -> list:
    _, _, mob = extract_map_object(map_data, symbol)
    _, _, other_mob = get_other_mob(map_data, symbol)
    weapon = getWeapons()[mob.get_weapon()]
    shield = getShields()[other_mob.get_shield()]
    log(symbol, f"You attack with {weapon.get_name()}!", "The dragon bites you!")
    damage = weapon.get_damage()
    shield_reduction = shield.get_defense()
    if shield_reduction > 0:
        damage = max(0, damage - shield_reduction)
        log(symbol, f"{shield.get_name()} absorbs {shield_reduction} damage", f"{shield.get_name()} absorbs {shield_reduction} damage")
        # durability is percent change shield is damaged
        if (100 * random.random()) < shield.get_durability():
            other_mob.set_shield(other_mob.get_shield() - 1)
            log(symbol, f"{shield.get_name()} is damaged", f"{shield.get_name()} is damaged")
    other_mob.set_health(other_mob.get_health() - damage)
    # does nothing for now
    return map_data

def can_breathe_fire(map_data: list, symbol: str) -> bool:
    motuple = extract_map_object(map_data, symbol)
    mob = motuple[2]
    if mob.get_breath_cooldown() or not mob.get_breath_timer():
        return False
    other_mob = get_other_mob(map_data, symbol)
    return not other_mob[2].get_is_burning() and distance((motuple[0], motuple[1]), (other_mob[0], other_mob[1])) <= mob.get_breath_range()

def breathe_fire(map_data: list, symbol: str) -> list:
    other_mob = get_other_mob(map_data, symbol)
    # if the dragon is within range of the player, the player is set on fire
    other_symbol = other_mob[2].get_symbol()
    log(other_symbol, "The dragon breathes fire on you", "The dragon giggles as you try to breathe fire on it.")
    if not other_mob[2].get_is_burning():
        if other_mob[2].get_is_wet():
            log(other_symbol, "Steam rises from your wet clothes.", "Steam rises from the dragon's scales.")
            other_mob[2].set_is_wet(False)
        else:
            other_mob[2].set_is_burning(True)
            log(other_symbol, "You are on fire!", "The dragon is on fire somehow!")
    
    weapon_index = other_mob[2].get_weapon()
    if weapon_index:
        weapon = getWeapons()[weapon_index]
        if weapon.get_can_be_tempered() and other_mob[2].get_carrying_ore():
            log(other_symbol, f"{weapon.get_name()} is tempered by the heat of the flames.", "The dragon's weapon is tempered by the heat.")
            other_mob[2].set_weapon(weapon_index + 1)
            other_mob[2].set_carrying_ore(False)
        elif not weapon.get_is_tempered():
            log(other_symbol, f"{weapon.get_name()} is melted by the heat.", "The dragon's weapon is melted by the heat.")
            other_mob[2].set_weapon(weapon_index - 1)

    motuple = extract_map_object(map_data, symbol)
    mob = motuple[2]
    mob.set_breath_cooldown(mob.get_breath_timer())
    return map_data

def can_pray(map_data: list, symbol: str) -> bool:
    # return True if the altar ('+') symbol is north of the player, False otherwise.
    x, y, player = extract_map_object(map_data, symbol)
    # if already blessed, return False
    if player.get_is_blessed():
        return False
    for mx, my, map_object in map_data:
        if map_object.get_symbol() == '*' and mx == x and my == y-1:
            return True
    return False

def pray(map_data: list, symbol: str) -> list:
    # make the player blessed
    player = extract_map_object(map_data, symbol)
    player[2].set_is_blessed(True)
    log(symbol, "You feel the favor of the gods upon you", "The dragon feels the favor of the gods upon it")
    return map_data

def can_bash(map_data: list, symbol: str) -> bool:
    # False is not holding a shield
    mob = extract_map_object(map_data, symbol)
    # return true if anything in the cardinal directions is destructible
    x, y, _ = extract_map_object(map_data, symbol)
    for dx, dy in ORTHOGONALS:
        new_x = x + dx
        new_y = y + dy
        for mx, my, map_object in map_data:
            if map_object.get_destructible() and mx == new_x and my == new_y:
                # if not ore, or player not carrying ore, return True
                if not map_object.get_is_ore() or (not mob[2].get_carrying_ore() and mob[2].get_shield()):
                    return True
    return False

def bash(map_data: list, symbol: str) -> list:
    # if there is something bashable in the four cardinal directions, there is a 25% chance it is removed
    x, y, player = extract_map_object(map_data, symbol)
    for dx, dy in ORTHOGONALS:
        new_x = x + dx
        new_y = y + dy
        for motuple in map_data:
            mx, my, map_object = motuple
            if map_object.get_destructible() and mx == new_x and my == new_y:
                # if map_object not is_ore, or player is not carrying ore, remove the object
                if random.random() < BASH_CHANCE:
                    # if the object is ore, set the player to be carrying ore
                    if map_object.get_is_ore():
                        player.set_carrying_ore(True)
                        log(symbol, "You pick up a lump of iron ore", "The dragon picks up a lump of iron ore")
                    if map_object.get_is_wood() and player.get_shield() < 3:
                        if not player.get_shield():
                            log(symbol, "You use a splintered piece of wood as a shield", "The dragon uses a splintered piece of wood as a shield")
                        else:
                            log(symbol, f"You upgrade your shield to {getShields()[player.get_shield() + 1]}", f"The dragon upgrades its shield to {getShields()[player.get_shield() + 1]}")
                        player.set_shield(player.get_shield() + 1)
                    del map_data[map_data.index(motuple)]
    return map_data

def can_quench(map_data: list, symbol: str) -> bool:
    # can quench if player has a tempered sword, is blessed, and is standing in a wet spot
    motuple = extract_map_object(map_data, symbol)
    x, y, player = motuple
    weapon = getWeapons()[player.get_weapon()]
    for mx, my, map_object in map_data:
        if map_object.get_wet() and mx == x and my == y:
            return weapon.get_can_be_blessed() and player.get_is_blessed()

    return False

def quench(map_data: list, symbol: str) -> list:
    # increase the weapon level by 1
    motuple = extract_map_object(map_data, symbol)
    player = motuple[2]
    player.set_weapon(player.get_weapon() + 1)
    weapon = getWeapons()[player.get_weapon()]
    log(symbol, f"You quench your weapon! The gods bless you with {weapon.get_name()}!", f"The gods bless the dragon with {weapon.get_name()}!")
    player.set_is_blessed(False)
    return map_data

def make_action_dictionary():
    # create a dictionary of actions
    action_dict = {}
    action_dict['h'] = (lambda map_data, symbol: move_mob(map_data, symbol, -1, 0), lambda map_data, symbol: direction_blocked(map_data, symbol, -1, 0), "move west")
    action_dict['j'] = (lambda map_data, symbol: move_mob(map_data, symbol, 0, 1), lambda map_data, symbol: direction_blocked(map_data, symbol, 0, 1), "move south")
    action_dict['k'] = (lambda map_data, symbol: move_mob(map_data, symbol, 0, -1), lambda map_data, symbol: direction_blocked(map_data, symbol, 0, -1), "move north")
    action_dict['l'] = (lambda map_data, symbol: move_mob(map_data, symbol, 1, 0), lambda map_data, symbol: direction_blocked(map_data, symbol, 1, 0), "move east")
    action_dict['a'] = (lambda map_data, symbol: attack(map_data, symbol), lambda map_data, symbol: not can_attack(map_data, symbol), "attack")
    action_dict['o'] = (lambda map_data, symbol: open_door(map_data, symbol), lambda map_data, symbol: not can_open_door(map_data, symbol), "open door")
    action_dict['p'] = (lambda map_data, symbol: pray(map_data, symbol), lambda map_data, symbol: not can_pray(map_data, symbol), "pray")
    action_dict['b'] = (lambda map_data, symbol: bash(map_data, symbol), lambda map_data, symbol: not can_bash(map_data, symbol), "bash")
    action_dict['B'] = (lambda map_data, symbol: breathe_fire(map_data, symbol), lambda map_data, symbol: not can_breathe_fire(map_data, symbol), "breathe fire")
    action_dict['q'] = (lambda map_data, symbol: quench(map_data, symbol), lambda map_data, symbol: not can_quench(map_data, symbol), "quench")
    action_dict['.'] = (lambda map_data, symbol: map_data, lambda map_data, symbol: False, "wait" )
    action_dict['Q'] = (lambda map_data, _: set_quit(map_data), lambda map_data, _: False, "quit")

    return action_dict

def decrement_cooldowns(map_data: list) -> list:
    # decrement the move cooldown of all mobile objects in map_data. return the updated map_data.
    for motuple in map_data:
        _, _, map_object = motuple
        if map_object.get_mobile() and map_object.get_move_cooldown() > 0:
            map_object.set_move_cooldown(map_object.get_move_cooldown() - 1)
        if map_object.get_mobile() and map_object.get_breath_cooldown() > 0:
            map_object.set_breath_cooldown(map_object.get_breath_cooldown() - 1)
    
    # if the player is burning, decrement health
    _, _, player = extract_map_object(map_data, PLAYER_SYMBOL)
    if player.get_is_burning() and player.get_health() > 0 and random.random() < BURN_CHANCE:
        player.set_health(player.get_health() - 1)
        log(PLAYER_SYMBOL, "You take 1 damage from the flames")

    return map_data

def display_valid_actions(stdscr, action_dict: dict, map_data: list, valid_actions: list):
    max_column_in_map = max([x for x, _, _ in map_data])
    stdscr.addstr(0, max_column_in_map+2, "Valid actions:")
    # display the list of valid actions
    for row, action in enumerate(valid_actions):
        stdscr.addstr(row+2, max_column_in_map+2, f"{action}: {action_dict[action][2]}")

def display_conditions(stdscr, map_data: list):
    max_column_in_map = max([x for x, _, _ in map_data])
    # display the conditions of the player
    _, _, player = extract_map_object(map_data, PLAYER_SYMBOL)
    stdscr.addstr(0, max_column_in_map+20, "Conditions:")
    condition_list = []
    if player.get_is_wet():
        condition_list.append("You are wet")
    if player.get_is_burning():
        condition_list.append("You are burning")
    if player.get_is_blessed():
        condition_list.append("You are blessed")
    if not condition_list:
        condition_list.append("You are fine")
    for row, condition in enumerate(condition_list):
        stdscr.addstr(row+2, max_column_in_map+20, condition)
    
    equipment_start_row = len(condition_list) + 3
    stdscr.addstr(equipment_start_row, max_column_in_map+20, "Equipment:")
    equipment = []
    equipment.append(f"Weapon: {getWeapons()[player.get_weapon()]}")
    equipment.append(f"Shield: {getShields()[player.get_shield()]}")
    if player.get_carrying_ore():
        equipment.append("Backpack: a lump of iron ore")
    else:
        equipment.append("Backpack: empty")
    for row, item in enumerate(equipment):
        stdscr.addstr(row+equipment_start_row+2, max_column_in_map+20, item)
    
    stdscr.addstr(15, 0, f"Health: {player.get_health()} Dragon: {get_other_mob(map_data, PLAYER_SYMBOL)[2].get_health()}")

def find_path(start: tuple, end: tuple, blocking_objects: list) -> list:
    # find the shortest path from start to end using A* search algorithm
    # return the path as a list of tuples
    queue = [(0, start[0], start[1], 0, 0)]  # Priority queue with (cost, x, y, dx, dy)
    visited = set()
    parent = {}
    heapq.heapify(queue)

    while queue:
        cost, x, y, dx, dy = heapq.heappop(queue)
        current = (x, y, dx, dy)
        if x == end[0] and y == end[1]:
            break
        visited.add((x, y))
        for dx, dy in ORTHOGONALS:
            new_x = x + dx
            new_y = y + dy
            if (new_x, new_y) in blocking_objects or (new_x, new_y) in visited:
                continue
            new_cost = cost + 1  # Assuming uniform cost for simplicity
            heapq.heappush(queue, (new_cost, new_x, new_y, dx, dy))
            new_current = (new_x, new_y, dx, dy)
            if new_current not in parent:
                parent[new_current] = current

    path = []
    while current[0] != start[0] or current[1] != start[1]:
        path.append(DXY_TO_COMMAND[(current[2], current[3])])
        current = parent[current]
    return path[::-1]

def log(symbol: str, pmessage: str, dmessage: str = "Missing message"):
    global global_log
    global_log.append((symbol, pmessage, dmessage))

def display_log(stdscr):
    global global_log
    for row, (symbol, pmessage, dmessage) in enumerate(global_log[-7:]):
        message = pmessage if symbol == PLAYER_SYMBOL else dmessage
        # if first character is lower case, capitalize it
        if message[0].islower():
            message = message[0].upper() + message[1:]
        # if final character is not punctuation, add a period
        if message[-1] not in ['.', '!', '?']:
            message += '.'
        stdscr.addstr(row+17, 0, f"{message}")

def determine_dragon_action(action_dict, map_data, dragon, player, blocking_objects):
    """
    Determines the next action for a dragon based on the available valid actions,
    the path to the player, and any blocking objects.

    Parameters:
    - action_dict: Dictionary mapping actions to their implementations and conditions.
    - map_data: Current state of the map.
    - dragon: The dragon for which to determine the action.
    - player: The player's current position.
    - blocking_objects: Objects that block movement on the map.

    Returns:
    - Updated map_data after applying the dragon's action.
    """
    # get valid actions for dragon, remove 'q' from list
    valid_actions = [key for key in action_dict if not action_dict[key][1](map_data, dragon[2].get_symbol()) and key not in ['Q', '.']]
    path = find_path(dragon, player, blocking_objects)

    if len(path) > 1 and path[0] in valid_actions:
        # Prioritize the first action in the path by making sure it's the last in the list
        valid_actions = [action for action in valid_actions if action not in ['l', 'j', 'k', 'h']] + [path[0]]

    if not valid_actions:
        # if the dragon has no valid actions, it waits
        action = '.'
    else:
        # randomly choose an action for the dragon
        action = random.choice(valid_actions)
        
    return action_dict[action][0](map_data, dragon[2].get_symbol())

def game_over(stdscr, map_data: list) -> bool:
    # game over if any of the mobile objects has zero health
    player = extract_map_object(map_data, PLAYER_SYMBOL)
    dragon = extract_map_object(map_data, DRAGON_SYMBOL)
    player_wins = player[2].get_health() > 0 and dragon[2].get_health() <= 0
    dragon_wins = dragon[2].get_health() > 0 and player[2].get_health() <= 0

    if player_wins or dragon_wins:
        # open a subwindow to display the game over message and prompt user to hit 'Q' to quit,
        # then wait for the user to press 'Q' to quit the game
        border_window = stdscr.subwin(5, 40, 10, 20)
        # fill border_window with '#' characters
        border_window.border()
        border_window.refresh()
        game_over_win = border_window.subwin(3, 38, 11, 21)
        # display window border
        messages = []
        messages.append("Game Over")
        messages.append("You defeated the dragon!" if player_wins else "The dragon slaughtered you...")
        messages.append("Press 'Q' to quit")
        game_over_width = game_over_win.getmaxyx()[1]
        # display the messages centered in the window
        for row, message in enumerate(messages):
            game_over_win.addstr(row, int((game_over_width - len(message))/2), message)

        game_over_win.refresh()
        while True:
            key = stdscr.getch()
            if chr(key) == 'Q':
                return True
    return False

global_quit = False
global_log = []

def main(stdscr):
    global global_quit, global_log
    map_data = load_map(map_file)
    action_dict = make_action_dictionary()
    # make a list of the coordinates of every blocking, non-mobile object

    # while the user has not pressed 'q', display the map
    while not global_quit:
        blocking_objects = [(mx, my) for mx, my, map_object in map_data if map_object.get_blocks() and not map_object.get_mobile()]
        map_data = decrement_cooldowns(map_data)

        stdscr.clear()
        display_map(stdscr, map_data)
        display_conditions(stdscr, map_data)
        player = extract_map_object(map_data, PLAYER_SYMBOL)

        # get list of all valid actions for player
        valid_actions = [key for key in action_dict if not action_dict[key][1](map_data, player[2].get_symbol())]

        display_valid_actions(stdscr, action_dict, map_data, valid_actions)
        display_log(stdscr)

        player = extract_map_object(map_data, PLAYER_SYMBOL)
        dragon = extract_map_object(map_data, DRAGON_SYMBOL)

        stdscr.refresh()

        if game_over(stdscr, map_data):
            break

        key = stdscr.getch()
        if chr(key) in valid_actions:
            map_data = action_dict[chr(key)][0](map_data, player[2].get_symbol())
        
        player = extract_map_object(map_data, PLAYER_SYMBOL)
        dragon = extract_map_object(map_data, DRAGON_SYMBOL)

        # determine dragon action
        map_data = determine_dragon_action(action_dict, map_data, dragon, player, blocking_objects)


if __name__ == '__main__':
    curses.wrapper(main)
