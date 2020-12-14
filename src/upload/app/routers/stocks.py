"""This module manages calls to yfinance package and the retrieveal of
its data"""

import json
from datetime import datetime
from fastapi import APIRouter
import yfinance as yf

router = APIRouter()


@router.get("/stocks/info", tags=["stocks"])
def store_general_info(ticker: str):
    """Recieve a ticker string and writes general information about the company
    to a json file and returns the dictionary"""
    stock = init_ticker(ticker)
    data = stock.info
    with open("stockData.json", "w") as outfile:
        json.dump(data, outfile, indent=4)
    return data


def init_ticker(name):
    """Checks tickers data returns the ticker object if data exists"""
    # create the ticker with uppercase letters
    ticker = yf.Ticker(name.upper())
    # check if there is data on this stock for the past week
    if len(ticker.history(period="1w")) == 0:
        raise ValueError(f"No data found for stock {name}")
    return ticker


@router.get("/stocks/stock", tags=["stocks"])
def get_data(ticker: str, start="", end="", interval="1d", period="ytd"):
    """Use yfinance to get stock data within a date range"""
    # Initialize the stock using the ticker string
    stock = init_ticker(ticker)
    # only sending a ticker and a start date uses the range (start-today)
    if (start != "") and (end == ""):
        print("this condition")
        data = stock.history(
            start=start, end=datetime.today().strftime("%Y-%m-%d"), interval=interval
        )
    # Check if both start and end has values
    elif not ((start == "") or (end == "")):
        data = stock.history(start=start, end=end, interval=interval)
    # Sending only the ticker to this function gets the maximum data with
    # daily inteval
    else:
        data = stock.history(interval=interval, period=period)

    return data.to_dict()


def main():
    """Main function"""
    data = get_data("tsla", start="2020-3-1")
    print(data)


if __name__ == "__main__":
    main()
