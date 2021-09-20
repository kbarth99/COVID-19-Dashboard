"""Importing Packages"""
import pandas as pd
import numpy as np
import requests
import dash
import dash_html_components as html
import plotly.graph_objects as go
import dash_core_components as dcc
from dash.dependencies import Input, Output


"""Importing Data"""
data = pd.read_json("https://data.cdc.gov/resource/9mfq-cb36.json?$limit=50000")
vaccinations = pd.read_json("https://data.cdc.gov/resource/unsk-b7fc.json?$limit=50000")
urbanpop = pd.read_excel('https://www2.census.gov/geo/docs/reference/ua/PctUrbanRural_State.xls')
vote = pd.read_excel("party.xlsx")
url = requests.get('https://worldpopulationreview.com/states')
df_list = pd.read_html(url.text)
popdf = df_list[0]
popdf = popdf.iloc[:,1:3]
popdf.rename(columns = {popdf.columns[1]:'pop'}, inplace = True)
urbanpop = urbanpop.iloc[:,np.r_[1,4]]
urbanpop.rename(columns = {urbanpop.columns[0]:'State',urbanpop.columns[1]:'citypop'}, inplace = True)
mergedf = pd.merge(vote, popdf, left_on='name',right_on='State').drop(columns = 'State')
mergedf = pd.merge(mergedf, urbanpop, left_on = 'name',right_on = 'State').drop(columns = 'State')
mergedf['citypop']=pd.cut(mergedf.citypop,bins = [0,mergedf.citypop.quantile(.5),mergedf.citypop.quantile(.66), max(mergedf.citypop)+1],labels=['Small','Medium','Large'])

"""Posturing Data"""
covid = data[['submission_date','state','new_case','new_death']]
covid['submission_date']=pd.to_datetime(covid['submission_date'])
covid.rename(columns={'submission_date':'date'}, inplace = True)

vaxed = vaccinations[['date','location','administered','series_complete_yes']]
vaxed.Date = pd.to_datetime(vaxed.date)
vaxed = vaxed.sort_values(['location','date'], ascending= [True, True]).reset_index()
vaxed.rename(columns={'location':'state'}, inplace = True)

for variable in ['administered','series_complete_yes']:
    new = []
    for index, row in vaxed.iterrows():
      if index == 0:
        new.append(0)
      elif vaxed.loc[index,'state'] != vaxed.loc[(index-1),'state']:
        new.append(0)
      else:
        val = vaxed.loc[index, variable] - vaxed.loc[(index-1), variable]
        new.append(val)
    if variable == 'administered':
        vaxed['new_administered'] = new
    else:
        vaxed['new_fully_vaxed'] = new
vaxed=vaxed.set_index('date')

for dailyormonthly in ['D','M']:
    
    """New Cases and Death Rates"""
    for variable in ['new_case','new_death']:
        df = pd.DataFrame(covid.set_index('date').groupby([pd.Grouper(freq=dailyormonthly),'state'])[variable].sum()).reset_index(level=['date','state'])
        df = pd.merge(df, mergedf, left_on='state', right_on='state').drop(columns = 'state')
        df[variable+'per100k'] = (df[variable]/df['pop'])*100000
        df=df.set_index('date')
        if variable == 'new_case':
            cases = df
        else:
            deaths = df
    
    """New Administration and Fully Vaccination Rates"""
    

    for variable in ['new_administered','new_fully_vaxed']:
        df = pd.DataFrame(vaxed.groupby([pd.Grouper(freq=dailyormonthly),'state'])[variable].sum()).reset_index(level=['date','state'])
        df = pd.merge(df, mergedf, left_on='state', right_on='state')
        df[variable+'per100k'] = (df[variable]/df['pop'])*100000
        df= df.set_index("date")
        if variable == 'new_administered':
            admin = df
        else:
            fullvax = df
        
    """Grouping and compiling"""
    
    if dailyormonthly == "D":
        dailycases2016 = pd.DataFrame(cases.groupby([pd.Grouper(freq=dailyormonthly),'party'])['new_caseper100k'].mean()).unstack()
        dailydeaths2016 = pd.DataFrame(deaths.groupby([pd.Grouper(freq=dailyormonthly),'party'])['new_deathper100k'].mean()).unstack()
        dailynewadmin2016 = pd.DataFrame(admin.groupby([pd.Grouper(freq=dailyormonthly),'party'])['new_administeredper100k'].mean()).unstack()
        dailynewvaxed2016 = pd.DataFrame(fullvax.groupby([pd.Grouper(freq=dailyormonthly),'party'])['new_fully_vaxedper100k'].mean()).unstack()
        dailycasessize = pd.DataFrame(cases.groupby([pd.Grouper(freq=dailyormonthly),'citypop'])['new_caseper100k'].mean()).unstack()
        dailydeathssize = pd.DataFrame(deaths.groupby([pd.Grouper(freq=dailyormonthly),'citypop'])['new_deathper100k'].mean()).unstack()
        dailynewadminsize = pd.DataFrame(admin.groupby([pd.Grouper(freq=dailyormonthly),'citypop'])['new_administeredper100k'].mean()).unstack()
        dailynewvaxedsize = pd.DataFrame(fullvax.groupby([pd.Grouper(freq=dailyormonthly),'citypop'])['new_fully_vaxedper100k'].mean()).unstack()
        finaldaily = dailycases2016.join(dailydeaths2016).join(dailynewadmin2016).join(dailynewvaxed2016).join(dailycasessize).join(dailydeathssize).join(dailynewadminsize).join(dailynewvaxedsize).fillna(0)
        finaldaily.columns = ['_'.join(col) for col in finaldaily.columns]
        for col in finaldaily:
            finaldaily[finaldaily[col]<0]=0
        

        
    else:
        monthlycases2016 = pd.DataFrame(cases.groupby([pd.Grouper(freq=dailyormonthly),'party'])['new_caseper100k'].mean()).unstack()
        monthlydeaths2016 = pd.DataFrame(deaths.groupby([pd.Grouper(freq=dailyormonthly),'party'])['new_deathper100k'].mean()).unstack()
        monthlynewadmin2016 = pd.DataFrame(admin.groupby([pd.Grouper(freq=dailyormonthly),'party'])['new_administeredper100k'].mean()).unstack()
        monthlynewvaxed2016 = pd.DataFrame(fullvax.groupby([pd.Grouper(freq=dailyormonthly),'party'])['new_fully_vaxedper100k'].mean()).unstack()
        monthlycasessize = pd.DataFrame(cases.groupby([pd.Grouper(freq=dailyormonthly),'citypop'])['new_caseper100k'].mean()).unstack()
        monthlydeathssize = pd.DataFrame(deaths.groupby([pd.Grouper(freq=dailyormonthly),'citypop'])['new_deathper100k'].mean()).unstack()
        monthlynewadminsize = pd.DataFrame(admin.groupby([pd.Grouper(freq=dailyormonthly),'citypop'])['new_administeredper100k'].mean()).unstack()
        monthlynewvaxedsize = pd.DataFrame(fullvax.groupby([pd.Grouper(freq=dailyormonthly),'citypop'])['new_fully_vaxedper100k'].mean()).unstack()
        finalmonthly = monthlycases2016.join(monthlydeaths2016).join(monthlynewadmin2016).join(monthlynewvaxed2016).join(monthlycasessize).join(monthlydeathssize).join(monthlynewadminsize).join(monthlynewvaxedsize).fillna(0)
        finalmonthly.columns = ['_'.join(col) for col in finalmonthly.columns]
        finalmonthly = finalmonthly.loc[np.logical_not(np.logical_and(finalmonthly.index.month == pd.Timestamp.today().month,finalmonthly.index.year == pd.Timestamp.today().year)),:]


"""Dashboard"""

app = dash.Dash(__name__, external_stylesheets= ['https://codepen.io/chriddyp/pen/bWLwgP.css'])
app.layout = html.Div(
    children = [
        html.Div(
            className = 'row', 
            children = [
                html.Div(
                    className = "four columns div-user-controls",
                    children = [
                        html.H2(children='COVID-19 Across Political Party and State Size'),
                        html.P("""Visualizing the Coronavirus Pandemic in States Based on Political Party (2016 Election) and Size of Urban Population (2010 Census)"""),
                        html.P("""This analysis does not imply causation between vote in the 2016 election and COVID-19 rates. Due to the vast area of the United States, waves of the Coronavirus are bound to hit different areas at different times.""")
                    ],
                ),
                html.Div(className="eight columns div-for-charts bg-grey",
                    children = [
                        dcc.Dropdown(id = 'dropdown3', options = [
                            {'label': 'Political Party', 'value':'Political'},
                            {'label':'Urban Population', 'value':'Urban'}],
                        value = 'Political'),
                        dcc.Dropdown(id = 'dropdown2', options = [
                            {'label': 'Daily', 'value':'Daily'},
                            {'label':'Monthly', 'value':'Monthly'}],
                        value = 'Daily'),
                        dcc.Dropdown(id = 'dropdown', options = [
                        {'label':'Cases', 'value':'new_caseper100k'},
                        {'label': 'Deaths', 'value':'new_deathper100k'},
                        {'label': 'Vaccinations Administered','value':'new_administeredper100k'},
                        {'label': 'Fully Vaccinated', 'value':'new_fully_vaxedper100k'}
                        ],
                        value = 'new_caseper100k',
                                    ),
                        dcc.Graph(id = 'bar_plot'),
                        ],
                    ),
                ],
            )
        ]
    )         
@app.callback(Output(component_id='bar_plot', component_property= 'figure'),
              [Input(component_id='dropdown', component_property= 'value'),Input(component_id='dropdown2',component_property = 'value'), Input(component_id = 'dropdown3',component_property='value')])
def graph_update(dropdown_value,dropdown2_value,dropdown3_value):
    print(dropdown_value)
    print(dropdown2_value)
    print(dropdown3_value)
    if dropdown2_value == "Monthly":
        df = finalmonthly
    else:
        df = finaldaily
    if dropdown3_value =='Political':
        uniquelist = ['Democrat','Republican']
    else:
        uniquelist = ['Small','Medium','Large']
    fig = go.Figure()
    for i in uniquelist:
        fig.add_trace(go.Scatter(x = df.index, y = df['{}'.format(dropdown_value)+'_'+i],
                            mode='lines',
                            name=i))

    
    fig.update_layout(title = 'Rates over Time In Average State',
                      xaxis_title = 'Date',
                      yaxis_title = 'New Occurances per 100K'
                      )
    fig.layout.template = 'simple_white'
    return fig  

if __name__ == '__main__': 
    app.run_server()
