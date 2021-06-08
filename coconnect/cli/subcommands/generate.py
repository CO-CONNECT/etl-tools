import os
import click
import coconnect
import pandas as pd
    
@click.group()
def generate():
    pass

@click.command(help="generate a python configuration for the given table")
@click.argument("table")
@click.argument("version")
def cdm(table,version):
    data_dir = os.path.dirname(coconnect.__file__)
    data_dir = f'{data_dir}/data/'

    version = 'v'+version.replace(".","_")
    
    #load the details of this cdm objects from the data files taken from OHDSI GitHub
    # - set the table (e.g. person, condition_occurrence,...)  as the index
    #   so that all values associated with the object (name) can be retrieved
    # - then set the field (e.g. person_id, birth_datetime,,) to help with future lookups
    # - just keep information on if the field is required (Yes/No) and what the datatype is (INTEGER,..)
    cdm = pd.read_csv(f'{data_dir}/cdm/OMOP_CDM_{version}.csv',encoding="ISO-8859-1")\
                 .set_index('table')\
                 .loc[table].set_index('field')[['required', 'type']]

    for index,row in cdm.iterrows():
        required = row['required'] == "Yes"
        dtype = row['type']
        string = f'self.{index} = DataType(dtype="{dtype}", required={required})'
        print (string)


@click.command(help="generate scan report json from input data")
@click.argument("inputs",
                nargs=-1)
def report(inputs):
    import pandas as pd
    import os
    import json

    m_ntop = 10

    data = []
    for fname in inputs:
        table_name = os.path.basename(fname)
        df = pd.read_csv(fname)
        column_names = df.columns.tolist()

        fields = []
        for col in column_names:
            series = df[col].value_counts(normalize=True).rename('frequency').round(4)
            if len(series)>=m_ntop:
                series = series.iloc[:m_ntop]

            frame = series.to_frame()
            values = frame.rename_axis('value').reset_index().to_dict(orient='records')
            fields.append({'field':col,'values':values})
            
        data.append({'table':table_name,'fields':fields})

    print (json.dumps(data,indent=6))
        
            
generate.add_command(report,"report")
generate.add_command(cdm,"cdm")

