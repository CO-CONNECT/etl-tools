from .objects import Person, ConditionOccurrence, VisitOccurrence

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


