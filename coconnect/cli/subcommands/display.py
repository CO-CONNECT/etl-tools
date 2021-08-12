import os
import click
import pandas
import json
import coconnect.tools as tools


@click.group(help='Commands for displaying various types of data and files.')
def display():
    pass

@click.command(help="Display a dataframe")
@click.argument('fname')
@click.option('--drop-na',is_flag=True)
@click.option('--markdown',is_flag=True)
@click.option('--head',type=int,default=None)
@click.option('--separator','--sep',type=str,default=None)
def dataframe(fname,drop_na,markdown,head,separator):

    #if separator not specified, get it from the file extension 
    if separator == None:
        separator = get_separator_from_filename(fname)
        
    df = pandas.read_csv(fname,nrows=head,sep=separator)
    if drop_na:
        df = df.dropna(axis=1,how='all')
    if markdown:
        df = df.to_markdown()
    print (df)

@click.command(help="plot from a csv file")
@click.argument('fnames',nargs=-1)
@click.option('-y',required=True,multiple=True)
@click.option('-x',required=True)
@click.option('--save-plot',default=None,help='choose the name of file to save the plot to')
def plot(fnames,x,y,save_plot):
    import matplotlib.pyplot as plt
    fig,ax = plt.subplots(len(y),figsize=(14,7))

    dfs = {
        fname:pandas.read_csv(fname)
        for fname in fnames
    }
    
    for i,_y in enumerate(y):
        ax[i].set_ylabel(_y)
        for fname in fnames:
            dfs[fname].plot(x=x,y=_y,ax=ax[i],label=fname)
    plt.show()
    if save_plot:
        fig.savefig(save_plot)


@click.command(help="Display the OMOP mapping json as a DAG")
@click.argument("rules")
def dag(rules):
    data = tools.load_json(rules)
    tools.make_dag(data['cdm'],render=True) 


@click.command(help="Show the OMOP mapping json")
@click.argument("rules")
@click.option('--list-tables',is_flag=True)
@click.option('--list-fields',is_flag=True)
def print_json(rules,list_fields,list_tables):
    data = tools.load_json(rules)
    if list_fields or list_tables:
        data = tools.get_mapped_fields_from_rules(data)
        if list_tables:
            data = list(data.keys())

    print (json.dumps(data,indent=6))


@click.command(help="Detect differences in either inputs or output csv files")
@click.option('--separator','--sep',type=str,default=None)
@click.option('--max-rows','-n',type=int,default=None)
@click.argument("file1")
@click.argument("file2")
def diff(file1,file2,separator,max_rows):
    tools.diff_csv(file1,file2,separator=separator,nrows=max_rows)


@click.command(help="flattern a rules json file")
@click.argument("rules")
def flatten(rules):
    data = tools.load_json(rules)
    objects = data['cdm']
    for destination_table,rule_set in objects.items():
        if len(rule_set) < 2: continue
        #print (rule_set)
        df = pd.DataFrame.from_records(rule_set).T

        #for name in df.index:
        #    print (name,len(df.loc[name]))

        df = df.loc['condition_concept_id'].apply(pd.Series)


        def merge(s):
            if s == 'term_mapping':
                print ('hiya')
                return {k:v for a in s for k,v in a.items()}
        
        print (df.groupby('source_field').agg(merge))
            
        #print (df.iloc[1])
        #print (df.iloc[1][1])
        #print (df)
        #print (df.iloc[0])
        #print (df.iloc[0].name)
        #print (df.iloc[0].apply(pd.Series))
        #print (df.iloc[1].apply(pd.Series)['term_mapping'].apply(pd.Series))
        
        exit(0)

                
display.add_command(dataframe,"dataframe")
display.add_command(dag,"dag")
display.add_command(print_json,"json")
display.add_command(plot,"plot")

display.add_command(diff,"diff")
display.add_command(flatten,"flatten")
