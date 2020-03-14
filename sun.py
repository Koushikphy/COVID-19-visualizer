import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
import dash_daq as daq
import flask
import numpy as np
import pandas as pd
import json

def parseData(dfc):
    total = dfc.sum(axis=0)[4:].values
    diff = np.append(total[0], np.diff(total))
    return np.vstack([total,diff])

def RawDataParser(file):
    global timeline  #???
    df = pd.read_csv(file)

    # drop countries/regions with 0 cases
    df = df.fillna(0)
    df = df[df[df.columns[-1]] != 0]
    timeline = pd.to_datetime(df.columns[4:], format='%m/%d/%y')
    fullData = {}

    for country in df["Country/Region"].unique():
        dfc = df[df['Country/Region'] == country]
        fullData[country] ={
            'data' : parseData(dfc),
            "states":None         # later states dic store same for the states
        } 
        if dfc.shape[0] !=1 : # states provided, modify the state key
            states = dfc['Province/State'].unique()
            fullData[country]["states"] = {
                state : parseData(dfc[dfc['Province/State'] == state]) for state in states
            }
    return fullData



sortedData = {
    "Confirmed" : RawDataParser('./time_series_19-covid-Confirmed.csv'),
    "Deaths":RawDataParser('./time_series_19-covid-Deaths.csv'),
    "Recovered":RawDataParser('./time_series_19-covid-Recovered.csv')
}
pieData={
    "Confirmed" : {k: v["data"][0,-1] for k,v in sortedData["Confirmed"].items()},
    "Deaths": {k: v["data"][0,-1] for k,v in sortedData["Deaths"].items()},
    "Recovered": {k: v["data"][0,-1] for k,v in sortedData["Recovered"].items()}
}

pieDataSelf = {}
for country in pieData["Confirmed"].keys():
    con = pieData["Confirmed"].get(country,0)
    dea = pieData["Deaths"].get(country, 0)
    rec = pieData["Recovered"].get(country, 0)
    suf = con - (dea+rec)
    pieDataSelf[country] = [suf,dea,rec]





def dicToSunBurst(country):
    labels, parents, values, allDat = [], [], [], {}
    for con in ["Confirmed","Deaths","Recovered"]:
        data = sortedData[con][country]
        allDat[con] ={}
        for k,v in data["states"].items():
            allDat[con][k] = v[0,-1]

    allDat['Suffering'] ={}
    for k,v in allDat["Confirmed"].items():
        suf = v - (allDat["Deaths"].get(k,0) + allDat["Recovered"].get(k,0) )
        allDat['Suffering'][k] = suf

    for con in ["Suffering","Deaths","Recovered"]:
        labels.append(con)
        parents.append('')
        values.append(sum(allDat[con].values()))
        for k,v in allDat[con].items():
            labels.append(k)
            parents.append(con)
            values.append(v)
    return labels, parents, values

lab, par, val = dicToSunBurst("US")
# print lab, par, val


def getPieOrSun(country):
    if sortedData["Confirmed"][country]["states"] is None: # return pie
        dat = [pieData["Confirmed"].get(country,0),
                pieData["Deaths"].get(country, 0), 
                pieData["Recovered"].get(country, 0) ]
        return [{
                "type": 'pie',
                'labels':["Suffering","Deaths","Recovered"],
                "values":dat,
                "textposition":'inside', 
                'textinfo':'percent+label',
                "showlegend": False,
            }]
    else:                                                       # return sun burst
        lab, par, val = dicToSunBurst(country)
        return [{
                    "type": 'sunburst',
                    "labels":lab,# ["India","WB","MP","RJ"],
                    "parents":par,#["","India","India","India"],
                    "values":val,#[24, 12, 10, 2],
                    'textinfo':'label',
                    'hoverinfo':'label+value+percent entry',
                    "showlegend": False,
                }]







# The GUI and server

server = flask.Flask('app')
app = dash.Dash('app', server=server)
app.title = 'COVID-19 visualizer'
app.scripts.config.serve_locally = False
dcc._js_dist[0]['external_url'] = 'https://cdn.plot.ly/plotly-basic-latest.min.js'

app.layout = html.Div([
    html.Div(
        children=[
            html.Label(
                'COVID-19 visualizer',
                style={'font-size': '27px', "font-weight":"bold",'float':'left', "margin-right":'75px',"font-family": "sans-serif"}
            ),
            html.Label(
                'Daily stat',
                style={'font-size': '21px', 'float':'left', 'margin-top':'5px'}
            ),
            daq.BooleanSwitch(
                id = 'dailyToggle',
                on=False,
                style={'float':'left', 'margin-top':'7px', "margin-right":'75px',"margin-left":"19px"}
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
                # value=[np.random.choice(sortedData['Confirmed'].keys())],
                value=["China"],
                multi=True ,
                placeholder ="Select Countries",
                style={"width":'85%',"margin-bottom":'5px'},
                persistence=False
            ),
        ],
        style={"border":"2px black solid"}
    ),

    html.Div(
        children=[
            dcc.Graph(
                id='piet',
                style = {"width":"25%",'float':'left',"height":"350px"},
                figure = {
                    'data': [{
                        "type": 'pie',
                        'labels':[],
                        "values":[],
                        "textposition":'inside', 
                        'textinfo':'percent+label',
                        "showlegend": False,
                    }],
                    "layout":{
                        "title":"",
                        "font":{
                            "size":"17",
                            "family":"Times New Roman"
                        }
                    }
                },
                config={"displayModeBar":False}
            ),
            dcc.Graph(
                id='pie1',
                style = {"width":"25%",'float':'left',"height":"350px"},
                figure = {
                    'data': [{
                        "type": 'pie',
                        'labels':pieData["Confirmed"].keys(),
                        "values":pieData["Confirmed"].values(),
                        "textposition":'inside', 
                        'textinfo':'percent+label',
                        "showlegend": False,
                    }],
                    "layout":{
                        "title":"Confirmed : " + "{}".format(sum(pieData["Confirmed"].values())),
                        "font":{
                            "size":"17",
                            "family":"Times New Roman"
                        }
                    }
                },
                config={"displayModeBar":False}
            ),
            dcc.Graph(
                id='pie2',
                style = {"width":"25%",'float':'left',"height":"350px"},
                figure = {
                    'data': [{
                        "type": 'pie',
                        'labels':pieData["Deaths"].keys(),
                        "values":pieData["Deaths"].values(),
                        "textposition":'inside', 
                        'textinfo':'percent+label',
                        "showlegend": False,
                    }],
                    "layout":{
                        "title":"Deaths : " + "{}".format(sum(pieData["Deaths"].values())),
                        "font":{
                            "size":"17",
                            "family":"Times New Roman",
                            "color":"red"
                        }
                    }
                },
                config={"displayModeBar":False}
            ),
            dcc.Graph(
                id='pie3',
                style = {"width":"25%",'float':'left',"height":"350px"},
                figure = {
                    'data': [{
                        "type": 'pie',
                        'labels':pieData["Recovered"].keys(),
                        "values":pieData["Recovered"].values(),
                        "textposition":'inside', 
                        'textinfo':'percent+label',
                        "showlegend": False,
                    }],
                    "layout":{
                        "title":"Recovered : " + "{}".format(sum(pieData["Recovered"].values())),
                        "font":{
                            "size":"17",
                            "family":"Times New Roman",
                            "color":"green"
                        }
                    }
                },
                config={"displayModeBar":False}
            )
        ],
        style={"width":'100%'}
    ),
    dcc.Graph(id='my-graph',style={"margin-top":'300px'},animate=True),
    dcc.Graph(
            id='pisun',
            # style = {"width":"25%",'float':'left'},
            figure = {
                'data': [{
                    "type": 'sunburst',
                    "labels":lab,# ["India","WB","MP","RJ"],
                    "parents":par,#["","India","India","India"],
                    "values":val,#[24, 12, 10, 2],
                    'textinfo':'label',
                    'hoverinfo':'label+value+percent entry',
                    "showlegend": False,
                }],
                "layout":{
                    "title":"",
                    "font":{
                        "size":"17",
                        "family":"Times New Roman"
                    }
                }
            },
        )
    ]
)

#updates the country list
@app.callback( Output('country', 'options'),
            [Input('condition', 'value')])
def countries(cond):
    return [{"label":i,"value":i} for i in sortedData[cond].keys()]


#updates the plot
@app.callback([Output('my-graph', 'figure'), Output('piet', 'figure')],
              [Input('country', 'value'),
              Input('dailyToggle', 'on'),
              Input('condition', 'value')])
def update_graph(value, dail, cond):
    data = []
    print(value, dail, cond)
    daily = 1 if dail else 0
    cond = str(cond)

    if((value is None) | (len(value)==0)):
        data.append({
            'x': [],
            "mode": "markers+lines",
            'y': [],
            'name' : value,
            'line': {
                'width': 3,
            }
        })
    else:
        for country in value:
            if(country not in sortedData[cond].keys()):
                data.append({
                    'x': timeline,
                    "mode": "markers+lines",
                    'y': np.zeros_like(timeline),
                    'name' : value,
                    'line': {
                        'width': 3,
                    }
                })
            else:
                dff = sortedData[cond][country]["data"][daily]
                data.append({
                    'x': timeline,
                    "mode": "markers+lines",
                    'y': dff,
                    'name' : country,
                    'line': {
                        'width': 3,
                    }
                })
        pie = {
            'data': getPieOrSun(country),
            "layout":{
                "title":"<b>"+str(country)+"</b>",
                "font":{
                    "size":"17",
                    "family":"Times New Roman"
                }
            }
        }


    figure =  {
        'data': data,
        'layout': {
            "title":cond,
            "font":{
                "size":"17",
                "family":"Times New Roman"
            }
        }
    }


    return figure, pie


if __name__ == '__main__':
    app.run_server(debug=True)
    # app.run_server(debug='False',port=8080,host='0.0.0.0')
