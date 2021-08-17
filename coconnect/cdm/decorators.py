from .objects import Person, ConditionOccurrence, VisitOccurrence, Measurement, Observation, DrugExposure

def from_table(table):
    def decorator(defs):
        def wrapper(obj):
            df = obj.inputs[table]
            for colname in df.columns:
                obj[colname].series = df[colname]
            return defs
        wrapper.__name__ = defs.__name__
        return wrapper
    return decorator

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
