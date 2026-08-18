import numpy as np

from inspect import signature

class Country:
    def __init__(self, name, resource, manpower, factory, logistic):
        self.name = name
        self.resource = resource
        self.manpower = manpower
        self.factory = factory
        self.logistic = logistic
        
    def static_battle(resource, manpower, factory, logistic):
        sig = signature(Country.static_battle)
        