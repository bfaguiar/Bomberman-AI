# Paulo Sousa, 80000
# Bruno Aguiar, 80177

import sys
import json
import asyncio
import websockets
import getpass
import os

from mapa import Map

from tree_search import *

import functools

import math

from characters import *

#########################################################################################################################

class Domain(SearchDomain):
                
    def __init__(self, mapa, enemies_list, extra = []):
        self.mapa = mapa
        self.enemies_list = enemies_list
        self.extra = extra
        
    def actions(self, state_bm):
        assert state_bm != None, "erro4"
        actlist = []
        x, y = state_bm
        neighborhood = [([x+1, y], "d"), ([x-1, y], "a"), ([x, y-1], "w"), ([x, y+1], "s")]
        for neighbor, key in neighborhood:
            if neighbor not in self.enemies_list:
                if neighbor not in self.extra:
                    if not self.mapa.is_stone(neighbor) and  not self.mapa.is_blocked(neighbor):
                        actlist.append(key)
        return actlist 

    def result(self, state_bm, action):
            newstate = state_bm[:]
            if action == "d":
                newstate[0] += 1
            elif action == "a":
                newstate[0] -= 1
            elif action == "w":
                newstate[1] -= 1
            elif action =="s":
                newstate[1] += 1
            return newstate                                                                                                                                                                               

    def cost(self, state_bm, action):
        return 1

    def heuristic(self, state_bm, goal_state):
        return math.hypot(state_bm[0] - goal_state[0], state_bm[1] - goal_state[1]) 

def sorted_bombs(state):
    return sorted(state["bombs"], key = lambda b: math.hypot(state["bomberman"][0] - b[0][0], state["bomberman"][1] - b[0][1]))

def sorted_enemies(state):
    return sorted(state["enemies"], key = lambda e: math.hypot(state["bomberman"][0] - e["pos"][0], state["bomberman"][1] - e["pos"][1]))

def sorted_powerups(state):
    return sorted(state["powerups"], key = lambda p: math.hypot(state["bomberman"][0] - p[0][0], state["bomberman"][1] - p[0][0]))

def sorted_walls(state):
    return sorted(state["walls"], key = lambda w: math.hypot(state["bomberman"][0] - w[0], state["bomberman"][1] - w[1]))

##################################################################################################################################

async def agent_loop(server_address="localhost:8000", agent_name="student"):
    async with websockets.connect(f"ws://{server_address}/player") as websocket:
        
        await websocket.send(json.dumps({"cmd": "join", "name": agent_name}))
        msg = await websocket.recv()
        game_properties = json.loads(msg)
        mapa = Map(size=game_properties["size"], mapa=game_properties["map"])

        keys = []
    
        def wreck_wall(state, domain, mapa, keys, extra = []):
            
            walls = sorted_walls(state)
            while(True):
                x, y = walls[0]
                domain = Domain(mapa, enemies_list, extra)
                neighborhood = [[x+1, y], [x-1, y], [x, y-1], [x, y+1]]
                cells = sorted([cell for cell in neighborhood if not mapa.is_stone(cell) and not mapa.is_blocked(cell)], 
                    key = lambda c: math.hypot(state["bomberman"][0] - c[0], state["bomberman"][1] - c[1]))
                if cells != []:
                    tree = SearchTree(SearchProblem(domain, state["bomberman"], cells[0])).search()
                    if tree == None:
                        walls = walls[1:]
                    else:
                        keys = tree[0]
                        keys.append("B")
                        break
                else: walls = walls[1:]
            return keys
        
        def inRange(state):
            x, y = state["bomberman"]
            bomb_range = []
            for i in range(1, 4):
                bomb_range = bomb_range + [[x+i, y], [x-i, y], [x, y-i], [x, y+i]]
            return any(e for e in state["enemies"] if e in bomb_range)
        
        def wreck_enemy(state, mapa, keys):
            enemy = sorted_enemies(state)[0]
            target = None
            a, b = None, None
            if enemy["name"] == "Balloom" or enemy["name"] == "Doll": 
                target = Balloom(enemy["pos"])
                for i in range(8):
                    target.move(mapa, state["bomberman"], state["bombs"], state["enemies"])
                a, b = target.pos
                x, y = state["bomberman"]
                bomb_trap = [n for n in [[a+1, b], [a-1, b], [a, b-1], [a, b+1]] if mapa.is_blocked(n) or mapa.is_stone(n)]
                if len(bomb_trap) == 3:
                    enemy_arg = target.pos
                    keys = wreck_wall(state,  domain, 
                    mapa, keys, target.pos)
                elif (x == a and y == b) or inRange(state):
                    keys = ["B"]
                else: 
                    tree = SearchTree(SearchProblem(domain, state["bomberman"], list(target.pos))).search()
                    if tree == None:
                        keys = keys + ['']
                    else:
                        keys = keys + [tree[0][0]]
                return keys
            else:
                ex, ey = enemy["pos"]
                target_array = sorted([cell for cell in [[ex+2, ey], [ex-2, ey], [ex, ey-2], [ex, ey+2]] if not mapa.is_blocked(cell) and not mapa.is_stone(cell)], key = lambda c: math.hypot(state["bomberman"][0] - c[0], state["bomberman"][1] - c[1]))
                if target_array == []:
                    keys = wreck_wall(state, domain, mapa, keys)
                else:
                    target = target_array[0]
                    a, b = target
                    x, y = state["bomberman"]
                    bomb_trap = [n for n in [[a+1, b], [a-1, b], [a, b-1], [a, b+1]] if mapa.is_blocked(n) or mapa.is_stone(n)]
                    if len(bomb_trap) == 3:
                        enemy_arg = target
                        keys = wreck_wall(state,  domain, mapa, keys, target)
                    elif (x == a and y == b) or inRange(state):
                        keys = ["B"]
                    else: 
                        tree = SearchTree(SearchProblem(domain, state["bomberman"], target)).search()
                        if tree == None:
                            keys = keys + ['']
                        else:
                            keys = keys + [tree[0][0]]
                return keys
        

        def waitexplode(state):
            if state["bombs"][0][1] > 0:
                pass 
        
        def bomb_space(state):
            x, y = sorted_bombs(state)[0][0]
            radius = sorted_bombs(state)[0][2]  
            neighborhood = []       
            for i in range(radius+1):
                neighborhood = neighborhood + [(x+i, y)]
                neighborhood = neighborhood + [(x, y+i)]
                neighborhood = neighborhood + [(x-i, y)]
                neighborhood = neighborhood + [(x, y-i)]
            neighborhood = list(set(neighborhood))
            neighborhood = [list(elem) for elem in neighborhood]
            return neighborhood

        def isSafePlace(state):
            neighborhood = bomb_space(state)
            return state["bomberman"] not in neighborhood

        def safe_cells(state, bomb):
            x, y = bomb
            count1, count2, count3, count4 = 0, 0, 0, 0
            quadrantes1 =  [[a, b] for a in range(x-15, x) for b in range(y-15, y) if a > 0 and b > 0] # 1
            quadrantes2 =  [[a, b] for a in range(x, x+15) for b in range(y-15, y) if a > 0 and b > 0] # 2
            quadrantes3 =  [[a, b] for a in range(x-15, x) for b in range(y, y+15) if a > 0 and b > 0] # 3 
            quadrantes4 =  [[a, b] for a in range(x, x+15) for b in range(y, y+15) if a > 0 and b > 0] # 4
            enemies_list = [e["pos"] for e in state["enemies"]]
            for e in enemies_list:
                if e in quadrantes1:
                    count1 = count1 + 1
                if e in quadrantes2:
                    count2 = count2 + 1
                if e in quadrantes3:
                    count3 = count3 + 1
                if e in quadrantes4:
                    count4 = count4 + 1
            q1 = {"quadrante" : quadrantes1, "count" : count1}
            q2 = {"quadrante" : quadrantes2, "count" : count2}
            q3 = {"quadrante" : quadrantes3, "count" : count3}
            q4 = {"quadrante" : quadrantes4, "count" : count4}
            choose_quadrants = sorted([q1, q2, q3, q4], key  = lambda k: k["count"])
            cells = []
            if choose_quadrants[0]["quadrante"] != []:
                bomb_neighborhood = bomb_space(state)
                aux = [coor for coor in choose_quadrants[0]["quadrante"] if coor not in enemies_list and not mapa.is_blocked(coor) and not mapa.is_stone(coor) and coor not in bomb_neighborhood]
                cells += sorted(aux, key = lambda k: math.hypot(state["bomberman"][0] - k[0], state["bomberman"][1] - k[1]))
            if choose_quadrants[1]["quadrante"] != []:
                bomb_neighborhood = bomb_space(state)
                aux = [coor for coor in choose_quadrants[1]["quadrante"] if coor not in enemies_list and not mapa.is_blocked(coor) and not mapa.is_stone(coor) and coor not in bomb_neighborhood]
                cells += sorted(aux, key = lambda k: math.hypot(state["bomberman"][0] - k[0], state["bomberman"][1] - k[1]))
            if choose_quadrants[2]["quadrante"] != []:
                bomb_neighborhood = bomb_space(state)
                aux = [coor for coor in choose_quadrants[2]["quadrante"] if coor not in enemies_list and not mapa.is_blocked(coor) and not mapa.is_stone(coor) and coor not in bomb_neighborhood]
                cells += sorted(aux, key = lambda k: math.hypot(state["bomberman"][0] - k[0], state["bomberman"][1] - k[1]))
            if choose_quadrants[3]["quadrante"] != []:
                bomb_neighborhood = bomb_space(state)
                aux = [coor for coor in choose_quadrants[3]["quadrante"] if coor not in enemies_list and not mapa.is_blocked(coor) and not mapa.is_stone(coor) and coor not in bomb_neighborhood]
                cells += sorted(aux, key = lambda k: math.hypot(state["bomberman"][0] - k[0], state["bomberman"][1] - k[1]))
            return cells 
        
        def runfrombomb(state, domain, cells):
                try:
                    tree = SearchTree(SearchProblem(domain, state["bomberman"], cells[0])).search()
                    if tree != None:
                        return tree[0]
                    else: 
                        return runfrombomb(state, domain, cells[1:])
                except IndexError: 
                    return ['']
                    
###############################################################################################################################

        pufound = False
        last_len = []
        levels = [] 
        while True:
            try:
                state = json.loads(
                    await websocket.recv() 
                )
               
                key = ""
                mapa.walls = state.get('walls')
                if levels != []:
                    level = levels.pop(0)
                    if level != state["level"]:
                        pufound = False
                levels.append(state["level"])

                if last_len == []:
                    last_len.append(len(state["enemies"]))       
                
                enemies_list = []
                if state["enemies"] != []:
                    for e in state["enemies"]: 
                        enemies_list.append(e["pos"])
                        if e["name"] == "Balloom" or e["name"] == "Doll":
                            x, y = e["pos"]
                            enemies_list.append([x+1, y])
                            enemies_list.append([x-1, y])
                            enemies_list.append([x, y-1])
                            enemies_list.append([x, y+1])
                
                domain = Domain(mapa, enemies_list)
                if state["bombs"] != []:
                    enemies_list = enemies_list + [bomb[0] for bomb in state["bombs"]]
                    domain = Domain(mapa, enemies_list, [bomb[0] for bomb in state["bombs"]])

                if keys == []:  
                    if state["bombs"] != []:
                        if isSafePlace(state):
                            keys=keys+["A"]  
                            waitexplode(state)
                        else:
                            keys = runfrombomb(state, domain, safe_cells(state, sorted_bombs(state)[0][0]))
                    
                    elif (state["step"] % 60 == 0 and state["walls"]!=[]):
                        last_len.append(len(state["enemies"]))
                        if last_len[-1] == last_len[-2] and state["enemies"] != []:
                            keys = wreck_wall(state, domain, mapa, keys)
                    
                    elif state["powerups"] != []:
                        keys = keys + [SearchTree(SearchProblem(domain, state["bomberman"], state["powerups"][0][0])).search()[0][0]]       
                        pufound = True                          

                    elif state["enemies"] != []:
                        receive = wreck_enemy(state, mapa, keys)
                        keys = keys + receive 
                    
                    elif state["exit"] != [] and pufound == True:
                            keys = keys + [SearchTree(SearchProblem(domain, state["bomberman"], state["exit"])).search()[0][0]] 
                    else: 
                        if state["walls"] != []:    
                            keys = wreck_wall(state, domain, mapa, keys)

                if keys != [] and keys != None:
                    key = keys.pop(0)   

                
                await websocket.send(
                    json.dumps({"cmd": "key", "key": key})
                )
                        
            except websockets.exceptions.ConnectionClosedOK:
                print("Server has cleanly disconnected us")
                return

loop = asyncio.get_event_loop()
SERVER = os.environ.get("SERVER", "localhost")
PORT = os.environ.get("PORT", "8000")
NAME = os.environ.get("NAME", getpass.getuser())
loop.run_until_complete(agent_loop(f"{SERVER}:{PORT}", NAME))
