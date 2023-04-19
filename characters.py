import yaml
import random

with open('alpha_config.yaml', 'r') as file:
    config = yaml.safe_load(file)
class CharacterClass:
    def __init__(self, character):
        self.character = character
        self.actions = []
        self.selectActions()
        self.printClassDetails()
    
    def printClassDetails(self):
        print(self.character, self.actions)
    
    # randomly select actions for the character type
    def selectActions(self):
        self.actions = random.sample(config['action_space'], random.randint(1, len(config['action_space'])))

# for testing
if __name__ == "__main__":
    characterList = random.sample(config['character'], random.randint(1, len(config['character'])))
    for character in characterList:
        CharacterClass(character)
    
    
    