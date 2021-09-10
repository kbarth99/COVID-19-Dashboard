"""Importing Packages"""
import pandas as pd
import numpy as np
import dash
import dash_html_components as html
import plotly.graph_objects as go
import dash_core_components as dcc
from dash.dependencies import Input, Output


"""Importing Data"""
data = pd.read_json("https://data.cdc.gov/resource/9mfq-cb36.json?$limit=50000")
vaccinations = pd.read_json("https://data.cdc.gov/resource/unsk-b7fc.json?$limit=50000")
vote = pd.read_excel("popandparty.xlsx")

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
        df = pd.merge(df, vote, left_on='state', right_on='State').drop(columns = 'State')
        df[variable+'per100k'] = (df[variable]/df['Pop'])*100000
        df=df.set_index('date')
        if variable == 'new_case':
            cases = df
        else:
            deaths = df
    
    """New Administration and Fully Vaccination Rates"""
    

    for variable in ['new_administered','new_fully_vaxed']:
        df = pd.DataFrame(vaxed.groupby([pd.Grouper(freq=dailyormonthly),'state'])[variable].sum()).reset_index(level=['date','state'])
        df = pd.merge(df, vote, left_on='state', right_on='State')
        df[variable+'per100k'] = (df[variable]/df['Pop'])*100000
        df= df.set_index("date")
        if variable == 'new_administered':
            admin = df
        else:
            fullvax = df
        
    """Grouping and compiling"""
    
    if dailyormonthly == "D":
        dailycases2016 = pd.DataFrame(cases.groupby([pd.Grouper(freq=dailyormonthly),'2016Party'])['new_caseper100k'].mean()).unstack()
        dailydeaths2016 = pd.DataFrame(deaths.groupby([pd.Grouper(freq=dailyormonthly),'2016Party'])['new_deathper100k'].mean()).unstack()
        dailynewadmin2016 = pd.DataFrame(admin.groupby([pd.Grouper(freq=dailyormonthly),'2016Party'])['new_administeredper100k'].mean()).unstack()
        dailynewvaxed2016 = pd.DataFrame(fullvax.groupby([pd.Grouper(freq=dailyormonthly),'2016Party'])['new_fully_vaxedper100k'].mean()).unstack()
        finaldaily = dailycases2016.join(dailydeaths2016).join(dailynewadmin2016).join(dailynewvaxed2016).fillna(0)
        finaldaily.columns = ['_'.join(col) for col in finaldaily.columns]
        
    else:
        monthlycases2016=pd.DataFrame(cases.groupby([pd.Grouper(freq=dailyormonthly),'2016Party'])['new_caseper100k'].mean()).unstack()
        monthlydeaths2016=pd.DataFrame(deaths.groupby([pd.Grouper(freq=dailyormonthly),'2016Party'])['new_deathper100k'].mean()).unstack()
        monthlyadmins2016=pd.DataFrame(admin.groupby([pd.Grouper(freq=dailyormonthly),'2016Party'])['new_administeredper100k'].mean()).unstack()
        monthlyfullvax2016=pd.DataFrame(fullvax.groupby([pd.Grouper(freq=dailyormonthly),'2016Party'])['new_fully_vaxedper100k'].mean()).unstack()
        finalmonthly = monthlycases2016.join(monthlydeaths2016).join(monthlyadmins2016).join(monthlyfullvax2016).fillna(0)
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
                        html.H2(children='COVID-19 in Democrat vs. Republican States'),
                        html.P("""Visualizing the Coronavirus Pandemic in States Based on Vote in 2016 Election in the United States"""),
                        html.P("""This analysis does not imply causation between vote in the 2016 election and COVID-19 rates. Due to the vast area of the United States, waves of the Coronavirus are bound to hit different areas at different times. Another confounding variable of this analysis is the number of urban centers within states.""")
                    ],
                ),
                html.Div(className="eight columns div-for-charts bg-grey",
                    children = [
                        
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
              [Input(component_id='dropdown', component_property= 'value'),Input(component_id='dropdown2',component_property = 'value')])
def graph_update(dropdown_value,dropdown2_value):
    print(dropdown_value)
    print(dropdown2_value)
    if dropdown2_value == "Monthly":
        df = finalmonthly
    else:
        df = finaldaily
    fig = go.Figure()
    fig.add_trace(go.Scatter(x = df.index, y = df['{}'.format(dropdown_value)+'_Democrat'],
                        mode='lines',
                        name='Democrat'))
    fig.add_trace(go.Scatter(x = df.index, y = df['{}'.format(dropdown_value)+'_Republican'],
                        mode='lines',
                        name='Republican'))
    
    fig.update_layout(title = 'Rates over Time In Average State',
                      xaxis_title = 'Date',
                      yaxis_title = 'New Occurances per 100K'
                      )
    fig.layout.template = 'simple_white'
    return fig  

if __name__ == '__main__': 
    app.run_server()