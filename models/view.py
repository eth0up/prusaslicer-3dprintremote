class View:
    def __init__(self, name, title=None, description=None, message=None, bag=dict(), error=None):
        self.Name = name
        self.Title = title
        self.Description = description
        self.Message = message
        self.Bag = bag
        self.Error = error
        
    def BagAdd(key, value):
        self.Bag[key] = value