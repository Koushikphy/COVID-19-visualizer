import pandas as pd

# download new data
def download():
    root = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/'
    files = ["time_series_19-covid-Confirmed.csv",'time_series_19-covid-Deaths.csv',"time_series_19-covid-Recovered.csv"]

    for file in files:
        df = pd.read_csv(root+file)
        df.to_csv(file, index=False)
download()