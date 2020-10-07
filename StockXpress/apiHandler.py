import requests
from requests.exceptions import HTTPError
from datetime import datetime

import logging
from logging.config import fileConfig

# This will add only error message from werkzeug to log file.
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# Loading logger configurations
fileConfig('logger_config.ini')
logger = logging.getLogger()

# Sample API url
# https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&apikey=NQCFKOVGZASY3EZ9&symbol=MSFT

# API parameters common to all requests:
__url__ = "https://www.alphavantage.co/query"
__function__ = "TIME_SERIES_DAILY_ADJUSTED"
__APIkey__ = "NQCFKOVGZASY3EZ9"


def convert_to_datetime(date):
    """Returns converted input date string into datetime object of format YYYY-MM-DD."""
    return datetime.strptime(date, '%Y-%m-%d')


def fetch_stock_data(symbol):
    """This will fetch necessary data of the given company from API.

    Args:
        symbol: (string) symbol of company

    Returns:
        Latest refresh_date and list of tuples of stock_data for passed company.

    Raises:
        ValueError for wrong company symbol.
    """
    try:
        parameter = {
            "function": __function__,
            "apikey": __APIkey__,
            "symbol": symbol
        }
        response = requests.get(__url__, params=parameter)
        response.raise_for_status()

        data = response.json()

        # If received symbol doesnt exists raise ValueError.
        if 'Error Message' in data:
            logger.error("Bad url request")
            raise ValueError("Invalid symbol. Please try again!")
        elif 'Note' in data:
            logger.error("API called more than 5 time in a min.")
            raise Exception("Max API call frequency reached.")

        refresh_date = data['Meta Data']['3. Last Refreshed']

        # If suppose Last Refreshed has time included.
        # e.g. 2019-07-31 13:30:13
        # then remove the time.
        refresh_date = refresh_date.split()[0]

        # Create list of data to be inserted into database.
        stock_data = [
            (date,
             factor['1. open'], factor['2. high'],
             factor['3. low'], factor['4. close'],
             factor['5. adjusted close'], factor['6. volume'],
             factor['7. dividend amount'], factor['8. split coefficient']
             ) for date, factor in data["Time Series (Daily)"].items()
        ]

        return refresh_date, stock_data

    except HTTPError as e:
        logger.error(e)


def get_refresh_date(symbol):
    """This will return (3. Last Refreshed) for the given company from API."""
    try:
        parameter = {
            "function": __function__,
            "apikey": __APIkey__,
            "symbol": symbol
        }
        response = requests.get(__url__, params=parameter)
        response.raise_for_status()

        data = response.json()
        refresh_date = data['Meta Data']['3. Last Refreshed']

        # If suppose Last Refreshed has time included.
        # e.g. 2019-07-31 13:30:13
        # then remove the time.
        refresh_date = refresh_date.split()[0]

        return refresh_date

    except Exception as e:
        logger.error(e)


def fetch_new_data(symbol, last_date):
    """This will only fetch new data that's not stored in database according to given last refresh date.

    Args:
        symbol: (string) Company symbol.
        last_date: (string) The last refreshed date for that company from database.

    Returns:
        list of new available stock data.
    """
    try:
        parameter = {
            "function": __function__,
            "apikey": __APIkey__,
            "symbol": symbol
        }
        response = requests.get(__url__, params=parameter)
        response.raise_for_status()
        data = response.json()

        last_date = convert_to_datetime(last_date)
        stock_data = [
            (date,
             factor['1. open'], factor['2. high'],
             factor['3. low'], factor['4. close'],
             factor['5. adjusted close'], factor['6. volume'],
             factor['7. dividend amount'], factor['8. split coefficient'])
            for date, factor in data["Time Series (Daily)"].items()
            if last_date < convert_to_datetime(date)
        ]
        return stock_data

    except HTTPError as e:
        logger.error(e)
