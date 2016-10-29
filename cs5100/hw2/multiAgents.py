# multiAgents.py
# --------------
# Licensing Information:  You are free to use or extend these projects for 
# educational purposes provided that (1) you do not distribute or publish 
# solutions, (2) you retain this notice, and (3) you provide clear 
# attribution to UC Berkeley, including a link to 
# http://inst.eecs.berkeley.edu/~cs188/pacman/pacman.html
# 
# Attribution Information: The Pacman AI projects were developed at UC Berkeley.
# The core projects and autograders were primarily created by John DeNero 
# (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# Student side autograding was added by Brad Miller, Nick Hay, and 
# Pieter Abbeel (pabbeel@cs.berkeley.edu).


from util import manhattanDistance, Queue, Stack
from game import Directions, Actions
import random, util
from math import floor, e
from game import Agent
from sys import maxint

PACMAN_INDEX = 0

class ReflexAgent(Agent):
    """
      A reflex agent chooses an action at each choice point by examining
      its alternatives via a state evaluation function.

      The code below is provided as a guide.  You are welcome to change
      it in any way you see fit, so long as you don't touch our method
      headers.
    """


    def getAction(self, gameState):
        """
        You do not need to change this method, but you're welcome to.

        getAction chooses among the best options according to the evaluation function.

        Just like in the previous project, getAction takes a GameState and returns
        some Directions.X for some X in the set {North, South, West, East, Stop}
        """
        # Collect legal moves and successor states
        legalMoves = gameState.getLegalActions()

        # Choose one of the best actions
        scores = [self.evaluationFunction(gameState, action) for action in legalMoves]
        bestScore = max(scores)
        bestIndices = [index for index in range(len(scores)) if scores[index] == bestScore]
        chosenIndex = random.choice(bestIndices) # Pick randomly among the best

        "Add more of your code here if you want to"

        return legalMoves[chosenIndex]

    def evaluationFunction(self, currentGameState, action):
        """
        Design a better evaluation function here.

        The evaluation function takes in the current and proposed successor
        GameStates (pacman.py) and returns a number, where higher numbers are better.

        The code below extracts some useful information from the state, like the
        remaining food (newFood) and Pacman position after moving (newPos).
        newScaredTimes holds the number of moves that each ghost will remain
        scared because of Pacman having eaten a power pellet.

        Print out these variables to see what you're getting, then combine them
        to create a masterful evaluation function.
        """
        # Useful information you can extract from a GameState (pacman.py)
        successorGameState = currentGameState.generatePacmanSuccessor(action)
        newPos = successorGameState.getPacmanPosition()
        newFood = successorGameState.getFood()
        newGhostStates = successorGameState.getGhostStates()
        newScaredTimes = [ghostState.scaredTimer for ghostState in newGhostStates]
        
        # initialize game info, distances to food, capsules, ghosts
        food = currentGameState.getFood()
        capsules = frozenset(currentGameState.getCapsules())
        food_dist = None
        ghosts = {
            tuple(floor(coord) for coord in ghost.getPosition()):
            ghost.scaredTimer for ghost in newGhostStates
        }
        if len(ghosts) == 0:
            ghost_dist = 0
            ghost_scared = 0
        else:
            ghost_dist = None
            ghost_scared = None
        queue = Queue()
        queue.push((newPos, 0))
        explored = set([currentGameState.getPacmanPosition()])
        walls = currentGameState.getWalls()
        
        # search for the nearest food and ghost
        while food_dist is None or ghost_dist is None:
            pos, dist = queue.pop()
            x, y = pos
            if food_dist is None and (food[x][y] or pos in capsules):
                food_dist = dist
            if ghost_dist is None and pos in ghosts:
                ghost_dist = dist
                ghost_scared = ghosts[pos]
            for neighbor in Actions.getLegalNeighbors(pos, walls):
                if neighbor not in explored:
                    explored.add(neighbor)
                    queue.push((neighbor, dist + 1))
                    
        # score close food, capsule, cared ghost high, close unscared ghost low
        if ghost_scared > 0:
            ghost_factor = 1.0
        else:
            ghost_factor = -3.0
        return 1.0 / (food_dist + 1) + ghost_factor / (ghost_dist + 1) ** 2

def scoreEvaluationFunction(currentGameState):
    """
      This default evaluation function just returns the score of the state.
      The score is the same one displayed in the Pacman GUI.

      This evaluation function is meant for use with adversarial search agents
      (not reflex agents).
    """
    return currentGameState.getScore()

class MultiAgentSearchAgent(Agent):
    """
      This class provides some common elements to all of your
      multi-agent searchers.  Any methods defined here will be available
      to the MinimaxPacmanAgent, AlphaBetaPacmanAgent & ExpectimaxPacmanAgent.

      You *do not* need to make any changes here, but you can if you want to
      add functionality to all your adversarial search agents.  Please do not
      remove anything, however.

      Note: this is an abstract class: one that should not be instantiated.  It's
      only partially specified, and designed to be extended.  Agent (game.py)
      is another abstract class.
    """

    def __init__(self, evalFn = 'scoreEvaluationFunction', depth = '2'):
        self.index = 0 # Pacman is always agent index 0
        self.evaluationFunction = util.lookup(evalFn, globals())
        self.depth = int(depth)

class MinimaxAgent(MultiAgentSearchAgent):
    """
      Your minimax agent (question 2)
    """

    def getAction(self, gameState):
        """
          Returns the minimax action from the current gameState using self.depth
          and self.evaluationFunction.

          Here are some method calls that might be useful when implementing minimax.

          gameState.getLegalActions(agentIndex):
            Returns a list of legal actions for an agent
            agentIndex=0 means Pacman, ghosts are >= 1

          gameState.generateSuccessor(agentIndex, action):
            Returns the successor game state after an agent takes an action

          gameState.getNumAgents():
            Returns the total number of agents in the game
        """
        return self._getAction(gameState, PACMAN_INDEX, 1)
            
    def _getAction(self, state, index, depth):
        # return the score if we're beyond the max depth
        if depth > self.depth:
            return self.evaluationFunction(state)
            
        # find all possible successor states
        actions = state.getLegalActions(index)
        if len(actions) == 0:
            successors = [state]
        else:
            successors = [
                state.generateSuccessor(index, action)
                for action in actions
            ]
            
        # score each successor state
        new_index = (index + 1) % state.getNumAgents()
        new_depth = depth + (new_index == PACMAN_INDEX)
        scores = [
            self._getAction(successor, new_index, new_depth)
            for successor in successors
        ]
        
        # return the best score or action
        choose = max if index == PACMAN_INDEX else min
        if index == PACMAN_INDEX and depth == 1:
            return actions[scores.index(choose(scores))]
        else:
            return choose(scores)
            
class AlphaBetaAgent(MultiAgentSearchAgent):
    """
      Your minimax agent with alpha-beta pruning (question 3)
    """

    def getAction(self, gameState):
        """
          Returns the minimax action using self.depth and self.evaluationFunction
        """
        return self._getAction(gameState, PACMAN_INDEX, 1, -maxint - 1, maxint)
        
    def _getAction(self, state, index, depth, alpha, beta):
        # return the score if we're beyond the max depth
        if depth > self.depth:
            return self.evaluationFunction(state)
            
        # find all possible actions
        actions = state.getLegalActions(index)
        if len(actions) == 0:
            actions = [None]
            
        # search the successor states with pruning
        scores = []
        best_score = -maxint - 1 if index == PACMAN_INDEX else maxint
        new_index = (index + 1) % state.getNumAgents()
        new_depth = depth + (new_index == PACMAN_INDEX)
        for action in actions:
            if action is None:
                successor = state
            else:
                successor = state.generateSuccessor(index, action)
            score = self._getAction(successor, new_index, new_depth, alpha, beta)
            scores.append(score)
            if index == PACMAN_INDEX:
                best_score = max(best_score, score)
                if best_score > beta:
                    break
                alpha = max(alpha, best_score)
            else:
                best_score = min(best_score, score)
                if best_score < alpha:
                    break
                beta = min(beta, best_score)
                    
        # return the best score or action
        if index == PACMAN_INDEX and depth == 1:
            return actions[scores.index(best_score)]
        else:
            return best_score
            
class ExpectimaxAgent(MultiAgentSearchAgent):
    """
      Your expectimax agent (question 4)
    """

    def getAction(self, gameState):
        """
          Returns the expectimax action using self.depth and self.evaluationFunction

          All ghosts should be modeled as choosing uniformly at random from their
          legal moves.
        """
        return self._getAction(gameState, PACMAN_INDEX, 1)
        
    def _getAction(self, state, index, depth):
        # return the score if we're beyond the max depth
        if depth > self.depth:
            return self.evaluationFunction(state)
            
        # find all possible successor states
        actions = state.getLegalActions(index)
        if len(actions) == 0:
            successors = [state]
        else:
            successors = [
                state.generateSuccessor(index, action)
                for action in actions
            ]
            
        # score each successor state
        new_index = (index + 1) % state.getNumAgents()
        new_depth = depth + (new_index == PACMAN_INDEX)
        scores = [
            self._getAction(successor, new_index, new_depth)
            for successor in successors
        ]
        
        # return the best score or action or an average
        if index == PACMAN_INDEX:
            if depth == 1:
                return actions[scores.index(max(scores))]
            else:
                return max(scores)
        else:
            return float(sum(scores)) / float(len(scores))
            
def betterEvaluationFunction(currentGameState):
    """
      Your extreme ghost-hunting, pellet-nabbing, food-gobbling, unstoppable
      evaluation function (question 5).

      The evaluation is the weighted sum of:
      - The current score
      - The reciprocal of the distance to the nearest pellet + 1
      - The negative reciprocal of the square of the distance to the nearest
        active ghost + 1 or the reciprocal of the square of the distance to
        the nearest scared ghost + 1
      - The reciprocal of the remaining capsules + 1
      
      This rewards increasing the score, consuming capsules, moving towards
      food and scared ghosts and penalizes moving towards an active ghost.
    """
    
    # initiate variables for search
    food = currentGameState.getFood()
    ghosts = {
        tuple(floor(coord) for coord in ghost.getPosition()):
        ghost.scaredTimer for ghost in currentGameState.getGhostStates()
    }
    food_dist = 0 if currentGameState.getNumFood() == 0 else None
    ghost_dist = ghost_scared = 0 if len(ghosts) == 0 else None
    walls = currentGameState.getWalls()
    
    # do search for closest ghost and food
    queue = Queue()
    queue.push((currentGameState.getPacmanPosition(), 0))
    explored = set([currentGameState.getPacmanPosition()])
    while food_dist is None or ghost_dist is None:
        pos, dist = queue.pop()
        x, y = pos
        if food_dist is None and (food[x][y]):
            food_dist = dist
        if ghost_dist is None and pos in ghosts:
            ghost_dist = dist
            ghost_scared = ghosts[pos]
        for neighbor in Actions.getLegalNeighbors(pos, walls):
            if neighbor not in explored:
                explored.add(neighbor)
                queue.push((neighbor, dist + 1))
           
    # evaluation for food distance
    food_eval = 1.0 / (food_dist + 1)
    
    # evaluation for ghosts
    if ghost_scared > 0:
        ghost_eval = 2.0 / (ghost_dist + 1) ** 2
    else:
        ghost_eval = -4.0 / (ghost_dist + 1) ** 2
    
    # evaluation for score
    score_eval = currentGameState.getScore()
    
    # evaluations for capsules left
    capsule_eval = 4.0 / (len(currentGameState.getCapsules()) + 1)
    
    # linear combination of evaluations
    return score_eval + food_eval + ghost_eval + capsule_eval
        
# Abbreviation
better = betterEvaluationFunction

