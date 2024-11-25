from fastapi import FastAPI
import joblib
import uvicorn
import pandas as pd
from pydantic import BaseModel
import openpyxl

class Market(BaseModel):
    commodity: str
    market: str
    duration: int

app = FastAPI()
joblib_in = open("min_price15days.joblib","rb")
model=joblib.load(joblib_in)

@app.get('/')
def index():
    return {'message': 'Minimum Price Prediction ML API'}

@app.post('/minprice/forecast')
def forcast_min_price(data:Market):
    data = data.dict()
    veg = data['commodity']
    market = data['market']
    duration = data['duration']

    dt = pd.date_range(start ='08-01-2023', end ='31-07-2024', freq ='D' )
    df = pd.read_excel('Book.xlsx',parse_dates=['Reported Date'],sheet_name = veg, index_col = 'Reported Date')
    df1_price_new = pd.DataFrame(columns=['Market Name','Min Price (Rs./Quintal)'],data=df,index=dt)
    df1_price_new['Market Name'].fillna(market,inplace=True)
    df1_price_new['Min Price (Rs./Quintal)'].fillna(method='bfill',inplace=True)
    df1_price_new['Min Price (Rs./Quintal)'].fillna(method='ffill',inplace=True)
    df1_price = pd.DataFrame(columns=['Market Name','Min Price (Rs./Quintal)'],data=df1_price_new)
    df1_price = df1_price.reset_index()
    df1_price.rename({'Market Name':'Market'},axis=1,inplace=True)
    df1_price = df1_price.rename({'Min Price (Rs./Quintal)':'y','index':'ds'},axis=1)

    df1_price['cap'] = min(df1_price['y']) + max(df1_price['y'])
    df1_price['floor'] = min(df1_price['y']) / 2

    future = model.make_future_dataframe(periods=duration)
    future['cap'] = min(df1_price['y']) + max(df1_price['y'])
    future['floor'] = min(df1_price['y']) / 2

    forecast = model.predict(future)
    forecast = forecast.rename(columns=({'yhat': 'market_price'}))
    forecast = forecast.rename(columns=({'ds': 'date'}))
   
    Price = forecast[['date','market_price']]
    Price['market_price'] = Price['market_price'].round(0)
    Price['date'] = Price['date'].dt.date
    Price.set_index('date', inplace=True)

    return {
        'veg': veg,
        'market' : market,
        'duration': duration,
        'forecast' : Price.tail(15)
    }

if __name__ == '__main__':
    uvicorn.run("main:app", port=8000, reload=True)
