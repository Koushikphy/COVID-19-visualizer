import sys
import numpy as np
import pandas as pd
import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
import dash_daq as daq
import flask


# download new files
def download():
    root = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/'
    files = ["time_series_19-covid-Confirmed.csv",'time_series_19-covid-Deaths.csv',"time_series_19-covid-Recovered.csv"]

    for file in files:
        df = pd.read_csv(root+file)
        df.to_csv(file, index=False)
# download()
##### Process data

def RawDataParser(file):
    global timeline  #???
    df = pd.read_csv(file)
    # drop countries/regions with 0 cases
    indexWithNoCase = df.index[df[df.columns[-1]] == 0].tolist()
    df = df.drop(df.index[indexWithNoCase])

    # Maybe later we can use Lat/Long to show location in a map
    df = df.drop(['Lat','Long'], axis=1)
    df = df.fillna(0)


    def parseData(df):
        df = df.drop(['Province/State', 'Country/Region'], axis=1)
        total = df.iloc[0].values
        diff = np.append(total[0], np.diff(total))
        return np.vstack([total,diff])

    sortedData = {}
    timeline = pd.to_datetime(df.columns[2:], format='%m/%d/%y')# every data has same timeline

    # I'm sure this can be done in more efficient way
    for country in df['Country/Region'].unique():
        # country= 'Italy'
        dfc = df[df['Country/Region'] == country]
        if dfc.shape[0] ==1 : # no state only country
            sortedData[country] = parseData(dfc)
        else: 
            #--> store for different states
            # sortedData[country] = {} # add another dictionary
            # states = dfc['Province/State'].unique()
            # for st in states:
            #     dfcs = dfc[dfc['Province/State'] == st]
            #     sortedData[country][st] = parseData(dfcs)
            #--> for now just merge all the states
            states = dfc['Province/State'].unique()
            val = parseData(dfc[dfc['Province/State'] == states[0]])
            for st in states:
                dfcs = dfc[dfc['Province/State'] == st]
                val +=parseData(dfc[dfc['Province/State'] == st])
            sortedData[country] = val
    return sortedData


sortedData = {
    "Confirmed" : RawDataParser('./time_series_19-covid-Confirmed.csv'),
    "Deaths":RawDataParser('./time_series_19-covid-Deaths.csv'),
    "Recovered":RawDataParser('./time_series_19-covid-Recovered.csv')
}


# The GUI and server

server = flask.Flask('app')
app = dash.Dash('app', server=server)
app.title = 'COVID-19 visualizer'
app.scripts.config.serve_locally = True
dcc._js_dist[0]['external_url'] = 'https://cdn.plot.ly/plotly-basic-latest.min.js'

app.layout = html.Div([
    html.H1('COVID-19 visualizer'),
    html.Div(children=[
    html.Label(
        'Daily stat',
        style={'font-size': '21px', 'float':'left', 'margin-top':'5px'}
    ),
    daq.BooleanSwitch(
        id = 'dailyToggle',
        on=False,
        style={'float':'left', 'margin-top':'5px', "margin-right":'75px',"margin-left":"19px"}
    ) ,
    dcc.RadioItems(
        id='condition',
        options=[
            {'label': 'Confirmed', 'value': 'Confirmed'},
            {'label': "Deaths", 'value': "Deaths"},
            {'label': "Recovered", 'value': "Recovered"}
            ],
        value='Confirmed',
        style={'font-size': '21px', 'margin-top':'5px', 'margin-bottom':'25px'}

    ),
    html.Label(
        'Countries',
        style={'font-size': '21px', 'margin-right':'21px','float':'left', 'margin-top':'5px'}
    ),
    dcc.Dropdown(
        id='country',
        options=[
            {"label":i,"value":i} for i in sorted(sortedData['Confirmed'].keys())
        ],
        # value="Italy",
        multi=True ,
        placeholder ="Select Countries",
        style={"width":'85%',"margin-bottom":'5px'},
    ),
    ], style={"border":"2px black solid"}),
    dcc.Graph(id='my-graph')
])



@app.callback( Output('country', 'options'),
            [Input('condition', 'value')])
def countries(cond):
    return [{"label":i,"value":i} for i in sortedData[cond].keys()]




@app.callback(Output('my-graph', 'figure'),
              [Input('country', 'value'),
              Input('dailyToggle', 'on'),
              Input('condition', 'value')])
def update_graph(value, dail, cond):
    data = []
    print value, dail, cond
    indd = 1 if dail else 0
    if(isinstance(value, basestring)):
        dff = sortedData[str(cond)][value][indd]
        data.append({
            'x': timeline,
            "mode": "markers+lines",
            'y': dff,
            'name' : value,
            'line': {
                'width': 3,
            }
        })
    else:
        for ind in value:
            dff = sortedData[str(cond)][ind][indd]
            data.append({
                'x': timeline,
                "mode": "markers+lines",
                'y': dff,
                'name' : ind,
                'line': {
                    'width': 3,
                }
            })
    return {
        'data': data,
        'layout': {'margin': {'l': 30,'r': 20,'b': 30,'t': 20}}
    }


if __name__ == '__main__':
    app.run_server(debug=True)