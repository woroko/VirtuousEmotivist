from mesa.visualization.ModularVisualization import ModularServer, VisualizationElement
from mesa.visualization.modules import CanvasGrid, ChartModule, TextElement
from mesa.visualization.UserParam import UserSettableParameter

from mesa.visualization.TextVisualization import (
    TextData, TextGrid, TextVisualization
)

from model import VirtuousEmotivistModel, EmotivistAgent, VirtuousAgent

import numpy as np
import string

GRID_WIDTH = 25
GRID_HEIGHT = 25
            
class HistogramModule(VisualizationElement):
    package_includes = ["Chart.min.js"]
    local_includes = ["HistogramModule.js"]

    def __init__(self, bins, canvas_height, canvas_width, type):
        self.canvas_height = canvas_height
        self.canvas_width = canvas_width
        self.bins = bins
        self.label_string = "Emotivist beliefs" if type == EmotivistAgent else "Virtuous beliefs"
        #self.label_string = "a"
        #print("LABELSTRING: " + self.label_string)
        self.type = type
        new_element = "new HistogramModule({}, {}, {}, \"{}\")"
        new_element = new_element.format(bins,
                                         canvas_width,
                                         canvas_height, self.label_string)
        self.js_code = "elements.push(" + new_element + ");"
    
    def render(self, model):
        if (type != None):
            belief_vals = [agent.strongest_belief() for agent in model.schedule.agents if isinstance(agent, self.type)]
        else:
            belief_vals = [agent.strongest_belief() for agent in model.schedule.agents]
        
        for i in range(0,len(belief_vals)):
            belief_vals[i] = string.ascii_lowercase.index(belief_vals[i].lower()) - string.ascii_lowercase.index('a')
        hist = np.histogram(belief_vals, bins=self.bins)[0]
        return [int(x) for x in hist]

class MiscMessageElement(TextElement):
    '''
    Display miscellaneous text
    '''

    def __init__(self):
        pass

    def render(self, model):
        return str(model.message)

class HappyElement(TextElement):
    '''
    Display a text count of how many happy agents there are.
    '''

    def __init__(self):
        pass

    def render(self, model):
        return "Happy agents: " + str(model.happy)
        
class ConvincedElement(TextElement):
    '''
    Display a text count of how many convinced agents there are.
    '''

    def __init__(self):
        pass

    def render(self, model):
        return "Convinced agents: " + str(model.convinced)


def ve_draw(agent):
    '''
    Portrayal Method for canvas
    '''
    if agent is None:
        return
    portrayal = {"Shape": "circle", "r": 0.8, "Filled": "false", "Layer": 0}

    if isinstance(agent, EmotivistAgent):
        portrayal["Color"] = ["#FF0000", "#FF9999"]
        portrayal["stroke_color"] = "#000000"
        if (agent.power > 1.0): #extra-powerful
            portrayal["stroke_color"] = "#FF0000"
        if (agent.determination > 0.0): #extra-determined
            portrayal["stroke_color"] = "#00FF00"
        if (agent.determination > 0.0 and agent.power > 1.0): #extra det+pow
            portrayal["stroke_color"] = "#FFFF00"
    else:
        portrayal["Color"] = ["#0000FF", "#9999FF"]
        portrayal["stroke_color"] = "#000000"
    portrayal["text"] = str(agent.strongest_belief())
    portrayal["text_color"] = "#000000"
    return portrayal


message_element = MiscMessageElement()
happy_element = HappyElement()
convinced_element = ConvincedElement()
canvas_element = CanvasGrid(ve_draw, GRID_HEIGHT, GRID_WIDTH, 500, 500)
happy_chart = ChartModule([{"Label": "happy", "Color": "Black"}])
convinced_chart = ChartModule([{"Label": "convinced", "Color": "Blue"}])
virtuous_vs_emotivist_chart = ChartModule([{"Label": "virtuous_count", "Color": "Blue"}, {"Label": "emotivist_count", "Color": "Red"} \
    , {"Label": "virtuous_death_count", "Color": "Black"}])

emo_belief_histogram = HistogramModule(list(range(4)), 400, 400, EmotivistAgent)
vir_belief_histogram = HistogramModule(list(range(4)), 400, 400, VirtuousAgent)


model_params = {
    "init_seed": 1,
    "height": GRID_HEIGHT,
    "width": GRID_WIDTH,
    "density": UserSettableParameter("slider", "Agent density", 0.8, 0.1, 0.975, 0.025),
    "minority_pc": UserSettableParameter("slider", "Fraction minority", 0.2, 0.00, 1.0, 0.05),
    "homophily": UserSettableParameter("slider", "Emotivist homophily", 2, 0, 8, 1),
    "virtuous_homophily": UserSettableParameter("slider", "VirtuousAgent homophily", 4, 0, 8, 1),
    "nudge_amount": UserSettableParameter("slider", "Amount to nudge belief", 0.01, 0, 0.2, 0.001),
    "num_to_argue": UserSettableParameter("slider", "Number of neighbors to argue with", 8, 0, 8, 1),
    "num_to_convert": UserSettableParameter("slider", "Number of emotivist neighbors to convert", 1, 0, 8, 1),
    "convert_prob": UserSettableParameter("slider", "Probability of conversion from emotivist to virtuous", 0.001, 0.0, 0.1, 0.001),
    "convinced_threshold": UserSettableParameter("slider", "Threshold of 'convinced' state", 0.98, 0.5, 1, 0.01),
    "random_move_prob": UserSettableParameter("slider", "Probability of random move", 0.0, 0.0, 0.2, 0.0025),
    "traditionless_life_decrease": UserSettableParameter("slider", "Amount of life loss when not in tradition", 0.01, 0.0, 0.2, 0.001),
    "vir_a": UserSettableParameter("slider", "Vir A", 0.3, 0, 1, 0.01),
    "vir_b": UserSettableParameter("slider", "Vir B", 0.4, 0, 1, 0.01),
    "vir_c": UserSettableParameter("slider", "Vir C", 0.3, 0, 1, 0.01),
    "emo_a": UserSettableParameter("slider", "Emo A", 0.3, 0, 1, 0.01),
    "emo_b": UserSettableParameter("slider", "Emo B", 0.4, 0, 1, 0.01),
    "emo_c": UserSettableParameter("slider", "Emo C", 0.3, 0, 1, 0.01),
    "emo_bias_a": UserSettableParameter("slider", "Emo bias against A", 1.0, 0, 1, 0.01),
    "emo_bias_b": UserSettableParameter("slider", "Emo bias against B", 1.0, 0, 1, 0.01),
    "emo_bias_c": UserSettableParameter("slider", "Emo bias against C", 1.0, 0, 1, 0.01),
    "strongest_belief_weight": UserSettableParameter("slider", "Starting weight of strongest belief", 0.7, 0, 1, 0.025),
    "count_extra_pow": UserSettableParameter("slider", "Number of extra-powerful emotivists (opportunists)", 0, 0, 200, 1),
    "count_extra_det": UserSettableParameter("slider", "Number of extra-determined emotivists (protestors)", 0, 0, 200, 1),
    "count_extra_det_pow": UserSettableParameter("slider", "Number of extra determined+powerful emotivists", 0, 0, 200, 1),
    "extra_pow": UserSettableParameter("slider", "Amount of extra power", 2, 1, 10, 0.25),
    "extra_det": UserSettableParameter("slider", "Amount of extra determination", 0.75, 0, 1, 0.025),
    "belief_of_extra_pow": UserSettableParameter("choice", "Belief of the extra-powerful", value='A', \
        choices=['A','B','C']),
    "belief_of_extra_det": UserSettableParameter("choice", "Belief of the extra-determined", value='A', \
        choices=['A','B','C']),
    "belief_of_extra_det_pow": UserSettableParameter("choice", "Belief of the extra determined+powerful", value='A', \
        choices=['A','B','C'])
    
    
}

server = ModularServer(VirtuousEmotivistModel,
                       [canvas_element, message_element, virtuous_vs_emotivist_chart, happy_element, happy_chart, convinced_element, convinced_chart, emo_belief_histogram \
                       , vir_belief_histogram],
                       "VirtuousEmotivist", model_params)
server.launch()
