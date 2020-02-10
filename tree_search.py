#  (c) Luis Seabra Lopes
# Edited by Bruno Aguiar, 80177

from abc import ABC, abstractmethod

# Dominios de pesquisa
# Permitem calcular
# as accoes possiveis em cada estado, etc
class SearchDomain(ABC):

    # construtor
    @abstractmethod
    def __init__(self):
        pass

    # lista de accoes possiveis num estado
    @abstractmethod
    def actions(self, state):
        pass

    # resultado de uma accao num estado, ou seja, o estado seguinte
    @abstractmethod
    def result(self, state, action):
        pass

    # custo de uma accao num estado
    @abstractmethod
    def cost(self, state, action):
        pass

    # custo estimado de chegar de um estado a outro
    @abstractmethod
    def heuristic(self, state, goal_state): 
        pass

# Problemas concretos a resolver
# dentro de um determinado dominio
class SearchProblem:
    def __init__(self, domain, initial, goal):
        self.domain = domain
        self.initial = initial
        self.goal = goal
    def goal_test(self, state):
        return state == self.goal

# Nos de uma arvore de pesquisa
class SearchNode:
    def __init__(self, state, parent,s_key, cost, heuristic): 
        self.state = state
        self.parent = parent
        self.s_key = s_key
        self.cost = cost 
        self.heuristic = heuristic

    def in_parent(self, state):
        if self.parent == None:
            return False

        return self.parent.state == state or self.parent.in_parent(state)

    def __str__(self):
        return f"no({self.state}, {self.s_key})"
    def __repr__(self):
        return str(self)

# Arvores de pesquisa
class SearchTree:

    # construtor
    def __init__(self,problem, ): 
        self.problem = problem
        self.root = SearchNode(problem.initial, None, "", 0, self.problem.domain.heuristic(problem.initial, problem.goal))
        self.open_nodes = [self.root]
        self.cost = 0
        self.length = 0

    # obter o caminho (sequencia de estados) da raiz ate um no
    def get_path(self,node):
        if node.parent == self.root or node.parent == None: # antes: node.parent == None # se der algum erro: filtrar as teclas vazias
            return [node.s_key]
        path = self.get_path(node.parent)
        path += [node.s_key]
        return(path)
    # procurar a solucao
    def search(self):
        while self.open_nodes != []:
            node = self.open_nodes.pop(0)
            self.cost += node.cost
            self.length += 1
            #print(self.problem.goal) 
            #print(self.length)
            if self.problem.goal_test(node.state):
                return self.get_path(node), node.cost
            elif self.length >= 50:
                return self.get_path(node), node.cost
            lnewnodes = []
            for a in self.problem.domain.actions(node.state):
                newstate = self.problem.domain.result(node.state,a)
                if not node.in_parent(newstate) and self.length < 50:
                    lnewnodes += [SearchNode(newstate,node, a, node.cost+self.problem.domain.cost(node.state,a), self.problem.domain.heuristic(newstate, self.problem.goal))]
            #self.open_nodes = sorted(self.open_nodes + lnewnodes, key=lambda node: node.heuristic + node.cost)
            self.open_nodes = sorted(self.open_nodes + lnewnodes, key=lambda node: node.heuristic)
        return None


