class Player():
    def __init__(self, name, color):
        self.name = name
        self.color = color
        self.score = 0
        self.meeples = 7
    
    def add_points(self, points):
        self.score += points
        
    def return_meeple(self):
        self.meeples += 1

    def place_meeple(self):
        self.meeples -= 1