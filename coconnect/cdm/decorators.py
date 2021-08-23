from .objects import Person, ConditionOccurrence, VisitOccurrence, Measurement, Observation, DrugExposure

def load_file(fname):
    def func(self):
        for colname in self.inputs[fname]:
            self[colname].series = self.inputs[fname][colname]
    func.__name__ = fname
    return func

def define_person(defs):
    p = Person()
    p.define = defs
    p.set_name(defs.__name__)
    return p

def define_condition_occurrence(defs):
    c = ConditionOccurrence()
    c.define = defs
    c.set_name(defs.__name__)
    return c

def define_visit_occurrence(defs):
    c = VisitOccurrence()
    c.define = defs
    c.set_name(defs.__name__)
    return c

def define_measurement(defs):
    c = Measurement()
    c.define = defs
    c.set_name(defs.__name__)
    return c

def define_observation(defs):
    c = Observation()
    c.define = defs
    c.set_name(defs.__name__)
    return c

def define_drug_exposure(defs):
    c = DrugExposure()
    c.define = defs
    c.set_name(defs.__name__)
    return c
