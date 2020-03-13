import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
import dash_daq as daq
import flask
import os
import sys
import numpy as np
import pandas as pd
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
    df = df.fillna(0)


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


# print sortedData["Confirmed"]
# for k,v in sortedData["Confirmed"].items():
#     print k, v[0,-1]
pieData={
    "Confirmed" : {k: v[0,-1] for k,v in sortedData["Confirmed"].items()},
    "Deaths": {k: v[0,-1] for k,v in sortedData["Deaths"].items()},
    "Recovered": {k: v[0,-1] for k,v in sortedData["Recovered"].items()}
}


pieDataSelf = {}
for country in pieData["Confirmed"].keys():
    con = pieData["Confirmed"][country]
    try:
        dea = pieData["Deaths"][country]
    except:
        dea=0
    try:
        rec = pieData["Recovered"][country]
    except:
        rec=0
    suf = con - (dea+rec)
    pieDataSelf[country] = [suf,dea,rec]
print pieDataSelf
# The GUI and server

server = flask.Flask('app')
app = dash.Dash('app', server=server)
app.title = 'COVID-19 visualizer'
app.scripts.config.serve_locally = False
dcc._js_dist[0]['external_url'] = 'https://cdn.plot.ly/plotly-basic-latest.min.js'

app.layout = html.Div([
    html.Div(children=[
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
        value=["China"],
        multi=True ,
        placeholder ="Select Countries",
        style={"width":'85%',"margin-bottom":'5px'},
    ),
    ], style={"border":"2px black solid"}),
    html.Div(children=[



    dcc.Graph(
        id='piet',
        style = {"width":"25%",'float':'left'},
        figure = {
        'data': [{
            "type": 'pie',
            'labels':[],#pieData["Deaths"].keys(),
            "values":[],#pieData["Deaths"].values(),
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
    }
    ),
    dcc.Graph(
        id='pie1',
        style = {"width":"25%",'float':'left'},
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
             "title":"Confirmed",
             "font":{
                 "size":"17",
                 "family":"Times New Roman"
             }
         }
    }),
    dcc.Graph(
        id='pie2',
        style = {"width":"25%",'float':'left'},
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
             "title":"Deaths",
             "font":{
                 "size":"17",
                 "family":"Times New Roman"
             }
         }
    }
    ),
    dcc.Graph(
        id='pie3',
        style = {"width":"25%",'float':'left'},
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
             "title":"Recovered",
             "font":{
                 "size":"17",
                 "family":"Times New Roman"
             }
         }
    }
    )],
    style={"width":'100%'}),
    dcc.Graph(id='my-graph',style={"margin-top":'400px'})
])


@app.callback( Output('country', 'options'),
            [Input('condition', 'value')])
def countries(cond):
    return [{"label":i,"value":i} for i in sortedData[cond].keys()]



@app.callback([Output('my-graph', 'figure'), Output('piet', 'figure')],
              [Input('country', 'value'),
              Input('dailyToggle', 'on'),
              Input('condition', 'value')])
def update_graph(value, dail, cond):
    data = []
    print(value, dail, cond)
    indd = 1 if dail else 0
    cond = str(cond)

    if(isinstance(value, basestring)):
        dff = sortedData[cond][value][indd]
        data.append({
            'x': timeline,
            "mode": "markers+lines",
            'y': dff,
            'name' : value,
            'line': {
                'width': 3,
            }
        })
    elif((value is None) | (len(value)==0)):
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
                dff = sortedData[cond][country][indd]
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
            'data': [{
                "type": 'pie',
                'labels':["Suffering","Deaths","Recovered"],#pieData["Deaths"].keys(),
                "values":pieDataSelf[country],#pieData["Deaths"].values(),
                "textposition":'inside', 
                'textinfo':'percent+label',
                "showlegend": False,
            }],
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
             }}
    }




    return figure, pie


if __name__ == '__main__':
    # app.run_server(debug=True)
    app.run_server(debug='False',port=8081,host='0.0.0.0')
