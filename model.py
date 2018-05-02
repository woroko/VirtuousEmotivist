import random
from math import ceil
import numpy as np

from mesa import Model, Agent
from mesa.time import RandomActivation
from mesa.space import SingleGrid
from mesa.datacollection import DataCollector

# random choice with probability
def random_decision(probability):
    return random.random() < probability

'''
Parameter changes from default, for situation where VirtuousAgents almost succeed
fraction minority: 0.3
neighbors to convert: 4
prob of random move: 0.03
VirtuousAgent homophily: 3
'''

class BelievingAgent(Agent):
    def __init__(self, unique_id, pos, model, initial_beliefs):
        '''
         Create a new believing agent.
        '''
        super().__init__(unique_id, model)
        self.pos = pos
        self.beliefs = initial_beliefs
        self.power = 1.0
        self.determination = 0.0
        self.happy = False
        self.convinced = False
        self.living = True
    
    # get the strongest belief
    # only returns the first belief if some are equally strong
    # change to return random belief
    def strongest_belief(self):
        return max(self.beliefs, key=self.beliefs.get)
    
    def beliefs_string(self):
        out = ""
        for belief, value in self.beliefs.items():
            out += belief + ": " + "{0:.2f}".format(value) + " "
        return out
    
    def die(self):
        self.model.grid._remove_agent(self.pos, self)
        self.model.schedule.remove(self)
        self.living = False
        
    
class EmotivistAgent(BelievingAgent):
    '''
    Emotivist agent.
    '''
    def __init__(self, unique_id, pos, model, initial_beliefs, initial_bias, initial_power, initial_determination):
        '''
         Create a new emotivist agent.
        '''
        super().__init__(unique_id, pos, model, initial_beliefs)
        self.bias = initial_bias
        self.power = initial_power
        self.determination = initial_determination
        
    def emotivist_argument(self, suggested_belief, suggestor_power):
        strongest_belief = self.strongest_belief()
        if (suggested_belief == strongest_belief):
            if (self.beliefs[strongest_belief] >= 1.0):
                return # already convinced
        # check if emotivist argument succeeds, adjust beliefs
        if (random_decision(self.bias[suggested_belief])):
            for belief in self.beliefs:
                if (belief == suggested_belief):
                    self.beliefs[belief] += (self.model.nudge_amount*suggestor_power*(1-self.determination))
                else:
                    self.beliefs[belief] -= (self.model.nudge_amount*suggestor_power*(1-self.determination)) / (len(self.beliefs)-1) # always normalize probs to 1.0

    def step(self):
        if (not self.living):
            return
    
        similar = 0
        randomly_moved = False
        strongest_belief = self.strongest_belief()
        #random moving
        if (random_decision(self.model.random_move_prob)):
            self.model.grid.move_to_empty(self)
            randomly_moved = True
        
        argued_with_count = 0
        # shuffle list of neighbors
        neighbors = list(self.model.grid.neighbor_iter(self.pos))
        random.shuffle(neighbors)
        for neighbor in neighbors:
            if isinstance(neighbor, type(self)):
                similar += 1
                if (argued_with_count < self.model.num_to_argue):
                    neighbor.emotivist_argument(strongest_belief, self.power) # argue with neighbor
                    argued_with_count += 1

        # If unhappy, move:
        if similar < self.model.homophily:
            self.happy = False
            if (not randomly_moved):
                self.model.grid.move_to_empty(self)
        else:
            self.happy = True
            
        if (self.beliefs[strongest_belief] >= self.model.convinced_threshold):
            self.convinced = True
        else:
            self.convinced = False

class VirtuousAgent(BelievingAgent):
    '''
    Virtuous agent
    '''
    def __init__(self, unique_id, pos, model, initial_beliefs, life_force = 1.0):
        '''
         Create a new Virtuous agent.
        '''
        super().__init__(unique_id, pos, model, initial_beliefs)
        self.life_force = life_force
    
    def strenghten_tradition(self, neighbor, suggested_belief):
        strongest_belief = self.strongest_belief()
        if (suggested_belief == strongest_belief):
            if (self.beliefs[strongest_belief] >= 1.0):
                return # already convinced
        # strenghten beliefs of neighbor, neighbor will strenghten in return
        for belief in neighbor.beliefs:
            if (belief == suggested_belief):
                neighbor.beliefs[belief] += self.model.nudge_amount
            else:
                neighbor.beliefs[belief] -= self.model.nudge_amount / (len(self.beliefs)-1) # always normalize probs to 1.0
                
    def convert_emotivist(self, neighbor, suggested_belief):
        neighbor_pos = neighbor.pos
        # destroy emotivist and replace with a new virtuous agent in the same tradition
        initial_strongestbelief_virtuous = suggested_belief
        initial_beliefs_virtuous = {}
        for belief in self.model.population:
            if (belief == initial_strongestbelief_virtuous):
                initial_beliefs_virtuous[belief] = self.model.strongest_belief_weight
            else:
                initial_beliefs_virtuous[belief] = (1-self.model.strongest_belief_weight)/(len(self.model.population)-1)
        agent = VirtuousAgent(self.model.last_agent_id, neighbor_pos, self.model, initial_beliefs_virtuous)
        self.model.last_agent_id += 1
        neighbor.die()
        self.model.grid.position_agent(agent, neighbor_pos)
        self.model.schedule.add(agent)
        #print("Converted: " + str(neighbor_pos))
    

    def step(self):
        if (not self.living):
            return
        
        similar = 0
        randomly_moved = False
        strongest_belief = self.strongest_belief()
        #random moving
        if (random_decision(self.model.random_move_prob)):
            self.model.grid.move_to_empty(self)
            randomly_moved = True
            
        tried_to_convert = 0
        
        # shuffle list of neighbors
        neighbors = list(self.model.grid.neighbor_iter(self.pos))
        random.shuffle(neighbors)
        # strenghten tradition and try to convert neighboring emotivists
        for neighbor in neighbors:
            if (isinstance(neighbor, type(self)) and neighbor.strongest_belief() == strongest_belief):
                similar += 1
                self.strenghten_tradition(neighbor, strongest_belief)
            elif (isinstance(neighbor, EmotivistAgent) and tried_to_convert < self.model.num_to_convert):
                if (random_decision(self.model.convert_prob)):
                    self.convert_emotivist(neighbor, strongest_belief)
                    tried_to_convert += 1

        # If unhappy, move:
        if similar < self.model.virtuous_homophily:
            self.happy = False
            #lose life force
            self.life_force -= self.model.traditionless_life_decrease / (similar+1)
            if (not randomly_moved):
                self.model.grid.move_to_empty(self)
        else:
            self.happy = True
            if (self.life_force < 1.0): #heal until over 1
                self.life_force += self.model.traditionless_life_decrease * similar
        
        if (self.beliefs[strongest_belief] >= self.model.convinced_threshold):
            self.convinced = True
        else:
            self.convinced = False
        
        # if life is too low, die
        if (self.life_force < 0.0):
            self.die()
            self.model.virtuous_death_count += 1

class VirtuousEmotivistModel(Model):
    '''
    Model class for the "Virtuous-Emotivist segregating opinion transfer model".
    '''

    def __init__(self, init_seed, height, width, density, minority_pc, homophily, virtuous_homophily, nudge_amount, num_to_argue, num_to_convert, convert_prob, convinced_threshold \
            , random_move_prob, traditionless_life_decrease, vir_a, vir_b, vir_c, emo_a, emo_b \
            , emo_c , emo_bias_a, emo_bias_b, emo_bias_c , strongest_belief_weight, count_extra_pow, count_extra_det \
            , count_extra_det_pow, extra_pow, extra_det , belief_of_extra_pow, belief_of_extra_det, belief_of_extra_det_pow):

        
        # uncomment to make runs reproducible
        #super().__init__(seed=init_seed)
        
        self.height = height
        self.width = width
        self.density = density
        self.minority_pc = minority_pc
        # segregation logic taken from the Schelling segregation model example
        self.homophily = homophily
        self.virtuous_homophily = virtuous_homophily
        self.convert_prob = convert_prob
        self.num_to_convert = num_to_convert
        self.traditionless_life_decrease = traditionless_life_decrease
        self.steps_since = 0
        
        self.schedule = RandomActivation(self)
        self.grid = SingleGrid(height, width, torus=True)
        
        self.happy = 0
        self.convinced = 0
        self.virtuous_count = 0
        self.emotivist_count = 0
        self.virtuous_death_count = 0
        self.datacollector = DataCollector( # Model-level variables for graphs
            {"happy": "happy", "convinced": "convinced", "emotivist_count": "emotivist_count" \
                , "virtuous_count": "virtuous_count", "virtuous_death_count": "virtuous_death_count"},  
            {"x": lambda a: a.pos[0], "y": lambda a: a.pos[1], "happy": lambda a: a.happy, # Agent-level variables
            "convinced": lambda a: a.convinced, "strongest_belief": lambda a: a.strongest_belief()
            , "beliefs": lambda a: a.beliefs_string(), "type": lambda a: 0 if isinstance(a, EmotivistAgent) else 1})
        
        self.nudge_amount = nudge_amount
        self.num_to_argue = num_to_argue
        self.convinced_threshold = convinced_threshold
        self.random_move_prob = random_move_prob
        
        population = ["A", "B", "C"] # defined here because of dependencies on the visualization side (emo_bias in server.py)
        self.population = population
        probs_emotivist = np.array([emo_a, emo_b, emo_c])
        probs_emotivist = probs_emotivist / np.sum(probs_emotivist) # normalize probs to 1.0
        probs_virtuous = np.array([vir_a, vir_b, vir_c])
        probs_virtuous = probs_virtuous / np.sum(probs_virtuous)
        initial_bias_emotivist = {"A": emo_bias_a, "B": emo_bias_b, "C": emo_bias_c}
        self.strongest_belief_weight = strongest_belief_weight
        
        # Set up agents
        # We get a list of cells in order from the grid iterator
        # and randomize the list
        cell_list = list(self.grid.coord_iter())
        random.shuffle(cell_list)
        total_num_agents = self.density*self.width*self.height
        
        det_emotivists_added = 0
        pow_emotivists_added = 0
        det_pow_emotivists_added = 0
        
        # pregenerate a list of strongest_beliefs in random order according to distribution
        # currently only works with a population of 3 beliefs
        list_emotivist_choices = []
        emo_length = ceil((1.0 - self.minority_pc)*total_num_agents)
        for i in range(0,emo_length):
            if (float(i)/emo_length < probs_emotivist[0]):
                list_emotivist_choices.append(population[0])
            elif (float(i)/emo_length < probs_emotivist[0]+probs_emotivist[1]):
                list_emotivist_choices.append(population[1])
            else:
                list_emotivist_choices.append(population[2])
        
        random.shuffle(list_emotivist_choices)
        
        list_virtuous_choices = []
        vir_length = ceil(self.minority_pc*total_num_agents)
        for i in range(0,vir_length):
            if (float(i)/vir_length < probs_virtuous[0]):
                list_virtuous_choices.append(population[0])
            elif (float(i)/vir_length < probs_virtuous[0]+probs_virtuous[1]):
                list_virtuous_choices.append(population[1])
            else:
                list_virtuous_choices.append(population[2])
        
        random.shuffle(list_virtuous_choices)
        
        # create agents and add to grid
        i=0
        for cell in cell_list:
            x = cell[1]
            y = cell[2]
            if i < total_num_agents:
                if i < self.minority_pc*total_num_agents:
                    #initial_strongestbelief_virtuous = random.choices(population, weights=probs_virtuous, k=1)[0]
                    initial_strongestbelief_virtuous = list_virtuous_choices.pop()
                    initial_beliefs_virtuous = {}
                    for belief in population:
                        if (belief == initial_strongestbelief_virtuous):
                            initial_beliefs_virtuous[belief] = strongest_belief_weight
                        else:
                            initial_beliefs_virtuous[belief] = (1-strongest_belief_weight)/(len(population)-1)
                    agent = VirtuousAgent(i, (x, y), self, initial_beliefs_virtuous)
                    self.virtuous_count += 1
                else:
                    #agent_type = 0
                    #initial_strongestbelief_emotivist = random.choices(population, weights=probs_emotivist, k=1)[0]
                    initial_strongestbelief_emotivist = list_emotivist_choices.pop()
                    initial_beliefs_emotivist = {}
                    det = 0.0
                    pow = 1.0
                    if (initial_strongestbelief_emotivist == belief_of_extra_det and det_emotivists_added < count_extra_det):
                        det = extra_det
                        det_emotivists_added += 1
                    elif (initial_strongestbelief_emotivist == belief_of_extra_pow and pow_emotivists_added < count_extra_pow):
                        pow = extra_pow
                        pow_emotivists_added += 1
                    elif (initial_strongestbelief_emotivist == belief_of_extra_det_pow and det_pow_emotivists_added < count_extra_det_pow):
                        pow = extra_pow
                        det_pow_emotivists_added += 1
                    
                    
                    for belief in population:
                        if (belief == initial_strongestbelief_emotivist):
                            initial_beliefs_emotivist[belief] = strongest_belief_weight
                        else:
                            initial_beliefs_emotivist[belief] = (1-strongest_belief_weight)/(len(population)-1)
                    
                    agent = EmotivistAgent(i, (x, y), self, initial_beliefs_emotivist, initial_bias_emotivist, pow, det)
                    self.emotivist_count += 1
                
                i += 1
                self.grid.position_agent(agent, (x, y))
                self.schedule.add(agent)
                
        self.last_agent_id = i
        # update message with starting probs
        self.message = "Emotivist probs: " + str(list(map(lambda x: "{:.2f}".format(x), probs_emotivist.tolist()))) \
                + ", Virtuous probs: " + str(list(map(lambda x: "{:.2f}".format(x), probs_virtuous.tolist())))
        self.running = True
        self.datacollector.collect(self)

    def update_emo_vir_count(self):
        emotivist_count = 0
        virtuous_count = 0
        for agent_type in self.datacollector.agent_vars["type"][-1]:
            if (agent_type[1] == 0):
                emotivist_count += 1
            else:
                virtuous_count += 1
        
        self.emotivist_count = emotivist_count
        self.virtuous_count = virtuous_count
        
    def update_happy_convinced_count(self):
        tmphappy = 0
        for agent_happy in self.datacollector.agent_vars["happy"][-1]:
            if (agent_happy[1]):
                tmphappy += 1
        tmpconvinced = 0
        for agent_convinced in self.datacollector.agent_vars["convinced"][-1]:
            if (agent_convinced[1]):
                tmpconvinced += 1

        self.happy = tmphappy
        self.convinced = tmpconvinced

        
    def step(self):
        '''
        Run one step of the model. Uncomment "self.running = False" to enable auto-stopping after the
        model has run for 200 steps with almost all agents happy and convinced
        '''
        # Reset counter of happy agents
        self.schedule.step()
        # collect data
        self.datacollector.collect(self)
        
        # update model-level counts
        self.update_happy_convinced_count()
        self.update_emo_vir_count()
        
        # optional auto-stopping
        if self.happy > self.schedule.get_agent_count()-3 and self.convinced == self.schedule.get_agent_count()-3:
            self.steps_since += 1
            if (self.steps_since > 200):
                #self.running = False
                pass
