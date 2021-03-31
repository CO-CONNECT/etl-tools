from jinja2 import Template

cls = Template(r'''
from coconnect.cdm import define_person, define_condition_occurrence, define_visit_occurrence, define_measurement

from coconnect.cdm import CommonDataModel
import json

class {{ name }}(CommonDataModel):
    {{ init }}
    {% for object in objects -%}
    {{ object }}
    {%- endfor %}

if __name__ == '__main__':
    {{ name }}()

''')

init = Template(r'''
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        {% if person_ids %}
        self.set_indexing({{ person_ids }})
        {% endif %}
''')

'''
{% for ds,pk in person_ids.items() -%}
        self.inputs["{{ ds }}"].index = self.inputs["{{ ds }}"]["{{ pk }}"].rename('index')
        {% endfor %} 
'''

rule = Template(r'''self.{{ destination_field }} = self.inputs["{{ source_table }}"]["{{ source_field }}"]''')

obj = Template(r'''
    @define_{{ object_name }}
    def {{ function_name }}(self):
        {% for rule in map_rules -%}
        {{ rule }}
        {% endfor %}
''')

