class Player():
    def __init__(self, name, color):
        self.name = name
        self.color = color
        self.score = 0
        self.meeples = 7
        self.is_remote = False
    
    def add_points(self, points):
        self.score += points
        
    def return_meeple(self):
        self.meeples += 1

    def place_meeple(self):
        self.meeples -= 1

    def clone(self):
        new_p = self.__class__.__new__(self.__class__)
        new_p.__dict__.update(self.__dict__)
        return new_p