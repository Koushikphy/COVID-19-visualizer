import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
import dash_daq as daq
import flask
import numpy as np
import pandas as pd

# TODO:
# improve update data function -> remove string check
# world wide statistics with sunburst
# country stat with sunburst for states
# improve inputs
# select multiple condition
# add acknowledgement
# add disclaimer


##### Process data

def RawDataParser(file):
    global timeline  #???
    df = pd.read_csv(file)
    # drop countries/regions with 0 cases
    indexWithNoCase = df.index[df[df.columns[-1]] == 0].tolist()
    df = df.drop(df.index[indexWithNoCase])
    df = df.fillna(0)
    # df = df[df.columns[-1]] /= 0]


    def parseData(country):
        total = df[df['Country/Region']==country].sum(axis=0)[4:].values
        diff = np.append(total[0], np.diff(total))
        return np.vstack([total,diff])

    timeline = pd.to_datetime(df.columns[4:], format='%m/%d/%y')# every data has same timeline
    return {country : parseData(country) for country in df['Country/Region'].unique()}


sortedData = {
    "Confirmed" : RawDataParser('./time_series_19-covid-Confirmed.csv'),
    "Deaths":RawDataParser('./time_series_19-covid-Deaths.csv'),
    "Recovered":RawDataParser('./time_series_19-covid-Recovered.csv')
}


pieData={
    "Confirmed" : {k: v[0,-1] for k,v in sortedData["Confirmed"].items()},
    "Deaths": {k: v[0,-1] for k,v in sortedData["Deaths"].items()},
    "Recovered": {k: v[0,-1] for k,v in sortedData["Recovered"].items()}
}


pieDataSelf = {}
for country in pieData["Confirmed"].keys():
    con = pieData["Confirmed"].get(country,0)
    dea = pieData["Deaths"].get(country, 0)
    rec = pieData["Recovered"].get(country, 0)
    suf = con - (dea+rec)
    pieDataSelf[country] = [suf,dea,rec]



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
            dcc.Checklist(
                id='condition',
                options=[
                    {'label': 'Confirmed', 'value': 'Confirmed'},
                    {'label': "Deaths", 'value': "Deaths"},
                    {'label': "Recovered", 'value': "Recovered"}
                    ],
                value=['Confirmed'],
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
                value=[np.random.choice(sortedData['Confirmed'].keys())],
                multi=True ,
                placeholder ="Select Countries",
                style={"width":'90%',"margin-bottom":'5px'},
            ),
        ],
        style={"border":"2px black solid", "margin-bottom":"17px"}
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
                        },
                        "margin":{"l":0,"r":0,"b":50,"t":40},
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
                        },
                        "margin":{"l":0,"r":0,"b":50,"t":40},
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
                        },
                        "margin":{"l":0,"r":0,"b":50,"t":40},
                    }
                },
                config={"displayModeBar":False}
            )
        ],
        style={"width":'100%'}
    ),
    dcc.Graph(id='my-graph',style={"margin-top":'350px'},animate=True),
        html.Label(
        'Data Source:',
        style={}
    ),
    ]
)

#updates the country list
@app.callback( Output('country', 'options'),
            [Input('condition', 'value')])
def countries(cond):
    if(len(cond)==0): return [{}] 
    return [{"label":i,"value":i} for i in sortedData["Confirmed"].keys()]


#updates the plot
@app.callback([Output('my-graph', 'figure'), Output('piet', 'figure')],
              [Input('country', 'value'),
              Input('dailyToggle', 'on'),
              Input('condition', 'value')])
def update_graph(value, dail, cond):
    data = []
    print(value, dail, cond, flask.request.remote_addr)
    indd = 1 if dail else 0


    maxVal = [0]
    legReq = len(cond)>1

    if((value is None) | (len(value)==0) | len(cond)==0):
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
        for con in cond:
            print con
            for country in value:
                if(country not in sortedData[con].keys()):
                    data.append({
                        'x': timeline,
                        "mode": "markers+lines",
                        'y': np.zeros_like(timeline),
                        'name' : '{}({})'.format(country, con),
                        'line': {'width': 3}
                    })
                else:
                    dff = sortedData[con][country][indd]
                    maxVal.append(max(dff))
                    data.append({
                        'x': timeline,
                        "mode": "markers+lines",
                        'y': dff,
                        'name' : '{}({})'.format(country, con),
                        'line': {'width': 3}
                    })

        pie = {
            'data': [{
                "type": 'pie',
                'labels':["Suffering","Deaths","Recovered"],
                "values":pieDataSelf[country],
                "textposition":'inside', 
                'textinfo':'percent+label',
                "showlegend": False,
            }],
            "layout":{
                "title":"<b>"+str(country)+"</b>",
                "font":{
                    "size":"17",
                    "family":"Times New Roman"
                },
            "margin":{"l":0,"r":0,"b":50,"t":40},
            }
        }


    mm = max(maxVal)

    figure =  {
        'data': data,
        'layout': {
            "font":{
                "size":"17",
                "family":"Times New Roman"
            },
            "yaxis":{
                "range":[0,mm*1.1]
            },
            "margin":{"l":35,"r":30,"b":25,"t":0},
            "legend":{"x":0,"y":.9}
        }
    }


    return figure, pie


if __name__ == '__main__':
    # app.run_server(debug=True)
    app.run_server(debug='False',port=8080,host='0.0.0.0')
