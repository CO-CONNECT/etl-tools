import os
import click
import json
import coconnect
import pandas as pd
import numpy as np
import requests
import secrets
import random
class MissingToken(Exception):
    pass


@click.group(help='Commands to generate helpful files.')
def generate():
    pass

@click.group(help='Commands to generate synthetic data.')
def synthetic():
    pass

@click.command(help="generate synthetic data from a ScanReport ID from CCOM")
@click.option("-i","--report-id",help="ScanReport ID on the website",required=True,type=int)
@click.option("-n","--number-of-events",help="number of rows to generate",required=True,type=int)
@click.option("-o","--output-directory",help="folder to save the synthetic data to",required=True,type=str)
@click.option("--fill-column-with-values",help="select columns to fill values for",multiple=True,type=str)
@click.option("-t","--token",help="specify the coconnect_token for accessing the CCOM website",type=str,default=None)
@click.option("--get-json",help="also download the json",is_flag=True)
@click.option("-u","--url",help="url endpoint for the CCOM website to ping",
              type=str,
              default="https://ccom.azurewebsites.net")
def ccom(report_id,number_of_events,output_directory,
         fill_column_with_values,token,get_json,
         url):

    fill_column_with_values = list(fill_column_with_values)
    
    token = os.environ.get("COCONNECT_TOKEN") or token
    if token == None:
        raise MissingToken("you must use the option --token or set the environment variable COCONNECT_TOKEN to be able to use this functionality. I.e  export COCONNECT_TOKEN=12345678 ")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36",
        "Content-type": "application/json",
        "charset": "utf-8",
        "Authorization": f"Token {token}"
    }
    
    if get_json:
        response = requests.get(
            f"{url}/api/json/?id={report_id}",
            headers=headers
        )
        print (json.dumps(response.json()[0],indent=6))
        fname = response.json()[0]['metadata']['dataset']
        with open(f'{fname}.json', 'w') as outfile:
            print ('saving',fname)
            json.dump(response.json()[0],outfile,indent=6)
            
    
    response = requests.get(
        f"{url}/api/scanreporttablesfilter/?scan_report={report_id}",
        headers=headers
    )
    if response.status_code != 200:
        print ('failed to get a response')
        print (response.json())
        exit(0)
    else:
        print (json.dumps(response.json(),indent=6))
        
    for table in response.json():
        name = table['name']
        _id = table['id']
        
        #get which is the person_id and automatically fill this with incrementing values
        #so they are not all NaN in the synthetic data (because of List Truncated...)
        person_id = table['person_id']
        if person_id == None:
            continue
        
        _url = f"{url}/api/scanreportfieldsfilter/?id={person_id}&fields=name"

        person_id = requests.get(
            _url, headers=headers,
            allow_redirects=True,
        ).json()[0]['name'].lstrip('\ufeff')
        
                
        _url = f"{url}/api/scanreportvaluesfilterscanreporttable/?scan_report_table={_id}&fields=value,frequency,scan_report_field"
        response = requests.get(
            _url, headers=headers,
            allow_redirects=True,
        )

                
        df = pd.DataFrame.from_records(response.json()).set_index('scan_report_field')        
        _url = f"{url}/api/scanreportfieldsfilter/?scan_report_table={_id}&fields=id,name"
        response = requests.get(
            _url, headers=headers,
            allow_redirects=True,
        )

        
        res = json.loads(response.content.decode('utf-8'))
        id_to_col_name = {
            field['id']:field['name'].lstrip('\ufeff')
            for field in res
        }
        
        df.index = df.index.map(id_to_col_name)

        
        df_synthetic = {}
        
        for col_name in df.index.unique():
            if col_name == '': continue
            
            _df = df.loc[[col_name]]
            _df['value'].replace('',np.nan,inplace=True)

            _df = _df.dropna()
            
            
            if len(_df) > number_of_events:
                _df = _df.sample(frac=1)[:number_of_events]

            
            frequency = _df['frequency']
            total = frequency.sum()

            
            if total > 0 :
                frequency = number_of_events*frequency / total
                frequency = frequency.astype(int)
            else:
                frequency = number_of_events
                
            values = _df['value'].repeat(frequency)\
                                 .sample(frac=1)\
                                 .reset_index(drop=True)

            values.name = col_name
            df_synthetic[col_name] = values

        df_synthetic = pd.concat(df_synthetic.values(),axis=1)
        
        
        for col_name in fill_column_with_values:
            if col_name in df_synthetic.columns:
                df_synthetic[col_name] = df_synthetic[col_name].reset_index()['index']
                
        
        if not os.path.isdir(output_directory):
            os.makedirs(output_directory)
        fname = f"{output_directory}/{name}"

        df_synthetic.index = 'pk'+df_synthetic.index.astype(str)
        df_synthetic.rename_axis(person_id,inplace=True)
        #df_synthetic.set_index(df_synthetic.columns[0],inplace=True)
        print (df_synthetic)
        df_synthetic.to_csv(fname)
        print (f"created {fname} with {number_of_events} events")
        
    
@click.command(help="generate synthetic data from a ScanReport xlsx file")
@click.argument("report")
@click.option("-n","--number-of-events",help="number of rows to generate",required=True,type=int)
@click.option("-o","--output-directory",help="folder to save the synthetic data to",required=True,type=str)
@click.option("--fill-column-with-values",help="select columns to fill values for",multiple=True,type=str)
def xlsx(report,number_of_events,output_directory,fill_column_with_values):
    dfs = pd.read_excel(report,sheet_name=None)
    sheets_to_process = list(dfs.keys())[2:-1]

    for name in sheets_to_process:
        df = dfs[name]
        columns_to_make = [
            x
            for x in df.columns
            if 'Frequency' not in x and 'Unnamed' not in x
        ]

        df_synthetic = {}
        for col_name in columns_to_make:
            i_col = df.columns.get_loc(col_name)
            df_stats = df.iloc[:,[i_col,i_col+1]].dropna()

            if not df_stats.empty:
                frequency = df_stats.iloc[:,1]
                frequency = number_of_events*frequency / frequency.sum()
                frequency = frequency.astype(int)

                values = df_stats.loc[df_stats.index.repeat(frequency)]\
                                 .iloc[:,0]\
                                 .sample(frac=1)\
                                 .reset_index(drop=True)
                df_synthetic[col_name] = values
            else:
                df_synthetic[col_name] = df_stats.iloc[:,0]
                
        df_synthetic = pd.concat(df_synthetic.values(),axis=1)

        for col_name in fill_column_with_values:
            if col_name in df_synthetic.columns:
                df_synthetic[col_name] = df_synthetic[col_name].reset_index()['index']
                
        
        if not os.path.isdir(output_directory):
            os.makedirs(output_directory)
        fname = f"{output_directory}/{name}"
        #ext = fname[-3:]
        df_synthetic.set_index(df_synthetic.columns[0],inplace=True)
        print (df_synthetic)
        df_synthetic.to_csv(fname)
        print (f"created {fname} with {number_of_events} events")


synthetic.add_command(xlsx,"xlsx")
synthetic.add_command(ccom,"ccom")
generate.add_command(synthetic,"synthetic")


        
@click.command(help="generate a python configuration for the given table")
@click.argument("table")
@click.argument("version")
def cdm(table,version):
    data_dir = os.path.dirname(coconnect.__file__)
    data_dir = f'{data_dir}{os.path.sep}data{os.path.sep}'
    data_dir = f'{data_dir}{os.path.sep}cdm{os.path.sep}BCLINK_EXPORT{os.path.sep}'
    
    #load the details of this cdm objects from the data files taken from OHDSI GitHub
    # - set the table (e.g. person, condition_occurrence,...)  as the index
    #   so that all values associated with the object (name) can be retrieved
    # - then set the field (e.g. person_id, birth_datetime,,) to help with future lookups
    # - just keep information on if the field is required (Yes/No) and what the datatype is (INTEGER,..)
    cdm = pd.read_csv(f'{data_dir}{version}{os.path.sep}export-{table.upper()}.csv',
                      encoding="ISO-8859-1",sep='\t')\
                      .set_index('DESCRIPTION')

    for index,row in cdm.iterrows():
        required = row['REQUIRED'] == "Yes"
        dtype = row['TYPE']
        length = row['LENGTH']
        key = row['KEY']
        
        if not np.isnan(length):
            dtype = f"{dtype}{int(length)}"

        if not np.isnan(key):
            extra = ', pk=True'
        else:
            extra = ''
            
        string = f'self.{index} = DestinationField(dtype="{dtype}", required={required} {extra})'
        print (string)
        
generate.add_command(cdm,"cdm")


@click.command(help="generate a hash token to be used as a salt")
@click.option("length","--length",default=64)
def salt(length):
    salt = secrets.token_hex(length)
    click.echo(salt)

generate.add_command(salt,"salt")


@click.command(help="generate scan report json from input data")
@click.option("max_distinct_values","--max-distinct-values",
              default=10,
              help='specify the maximum number of distinct values to include in the ScanReport.')
@click.option("min_cell_count","--min-cell-count",
              default=5,
              help='specify the minimum number of occurrences of a cell value before it can appear in the ScanReport.')
@click.option("rows_per_table","--rows-per-table",
              default=None,
              help='specify the maximum of rows to scan per input data file (table).')
@click.option("randomise","--randomise",
              default=True,
              help='randomise rows')
@click.argument("inputs",
                nargs=-1)
def report(inputs,max_distinct_values,min_cell_count,rows_per_table,randomise):
    skiprows = None
    #p = 0.1
    #skiprows=lambda i: i>0 and random.random() > p
        
    data = []
    for fname in inputs:
        #get the name of the data table
        table_name = os.path.basename(fname)
        #load as a pandas dataframe
        #load it and preserve the original data (i.e. no NaN conversions)
        df = pd.read_csv(fname,
                         dtype=str,
                         keep_default_na=False,
                         nrows=rows_per_table,
                         skiprows=None)
        #get a list of all column (field) names
        column_names = df.columns.tolist()
        fields = []
        #loop over all colimns
        for col in column_names:
            #value count the columns
            series = df[col].value_counts()
            #reduce the size of the value counts depending on specifications of max distinct values 
            if max_distinct_values>0 and len(series)>=max_distinct_values:
                series = series.iloc[:max_distinct_values]

            #if the min cell count is set, remove value counts that are below this threshold
            if not min_cell_count is None:
                series = series[series >= min_cell_count]

            #convert into a frequency instead of value count
            series = (series/len(df)).rename('frequency').round(4) 

            #convert the values to a dictionary 
            frame = series.to_frame()
            values = frame.rename_axis('value').reset_index().to_dict(orient='records')
            #record the value (frequency counts) for this field
            fields.append({'field':col,'values':values})

        meta = {
            'nscanned':len(df),
            'max_distinct_values':max_distinct_values,
            'min_cell_count':min_cell_count
        }
        data.append({'table':table_name,'fields':fields, 'meta':meta})

    click.echo(json.dumps(data,indent=6))
            
generate.add_command(report,"report")


@click.command(help="Generate synthetic data from the json format of the scan report")
@click.option("-n","--number-of-events",help="number of rows to generate",required=True,type=int)
@click.option("-o","--output-directory",help="folder to save the synthetic data to",required=True,type=str)
@click.option("--fill-column-with-values",help="select columns to fill values for",multiple=True,type=str)
@click.argument("f_in")
def synthetic_from_json(f_in,number_of_events,output_directory,fill_column_with_values):
    fill_column_with_values = list(fill_column_with_values)
    report = json.load(open(f_in))
    for table in report:
        table_name = table['table']
        fields = table['fields']
        df_synthetic = {}
        for field in fields:
            field_name = field['field']
            values = field['values']
            df = pd.DataFrame.from_records(values)
            if len(df) == 0:
                values = pd.Series([])
            else:
                frequency = df['frequency']
                frequency = number_of_events*frequency / frequency.sum()
                frequency = frequency.astype(int)
                values = df['value'].repeat(frequency).sample(frac=1).reset_index(drop=True)
            values.name = field_name
            
            df_synthetic[field_name] = values
            #else:
            #    df_synthetic[col_name] = df_stats.iloc[:,0]
                
        df_synthetic = pd.concat(df_synthetic.values(),axis=1)
        for col_name in fill_column_with_values:
            if col_name in df_synthetic.columns:
                df_synthetic[col_name] = df_synthetic[col_name].reset_index()['index']

        df_synthetic.set_index(df_synthetic.columns[0],inplace=True)

        if not os.path.isdir(output_directory):
            os.makedirs(output_directory)
        fname = f"{output_directory}/{table_name}"

        #df_synthetic.index = 'pk'+df_synthetic.index.astype(str)
        #df_synthetic.rename_axis(person_id,inplace=True)
        #df_synthetic.set_index(df_synthetic.columns[0],inplace=True)
        click.echo(df_synthetic)
        df_synthetic.to_csv(fname)
        click.echo(f"created {fname} with {number_of_events} events")


synthetic.add_command(synthetic_from_json,"json")


@click.command(help="convert the json report into a xlsx sheet")
@click.option("-o","--output",help="name of the output xlsx file",type=str,default=None)
@click.argument("f_in")
def report_to_xlsx(f_in,output):
    report = json.load(open(f_in))

    if output == None:
        output = f_in.replace(".json",".xlsx")

    with pd.ExcelWriter(output) as writer:  
        for table in report:
            table_name = table['table']
            total = []
            for field in table['fields']:
                field_name = field['field']
                values = field['values']
                data = pd.DataFrame.from_records(values)
                columns = [field_name,'Frequency']
                if data.empty:
                    data = pd.DataFrame(columns=columns)
                else:
                    data.columns=columns
                    total.append(data)
            df = pd.concat(total,axis=1)
            print (df)
            df.to_excel(writer, sheet_name=table_name, index=False)
            
                
generate.add_command(report_to_xlsx,"xlsx")

