import apiHandler
import dbHandler as db
import json
from datetime import datetime

import logging
from logging.config import fileConfig

# This will add only error message from werkzeug to log file.
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# Loading logger configurations
fileConfig('logger_config.ini')
logger = logging.getLogger()


def write_to_file(symbol, record):
    """This will write passed record to JSON file with name as 'sym_accesstime.json'.

    Args:
        symbol: (string) Company symbol.
        record: Dictionary of stock record entry.

    Returns:
        None
    """
    record["recorded_date"] = str(record["recorded_date"])
    dic = {"symbol": symbol, "Stock_record": record}

    filename = "{}_{}.json".format(symbol, datetime.now())
    filepath = './output/' + filename

    with open(filepath, 'w') as outfile:
        json.dump(dic, outfile, indent=4)
        logger.info("Records written to file successfully!")


def load_new_company(symbol):
    """This will load new company's stock data to the database.

    Args:
        symbol: (string) Company symbol.

    Returns:
        a boolean status of operation and related message.
        True if operation is completed successfully, false with error message otherwise.
    """
    try:
        already_loaded = db.get_companies()

        # Check if data for that company is already loaded.
        if symbol in already_loaded:
            return False, "Data for {} already loaded.".format(symbol)
        else:
            # Consume data from API.
            refresh_date, stock_data = apiHandler.fetch_stock_data(symbol)

            # Add company entry in meta data table.
            db.add_company_data(symbol, refresh_date)

            # Create separate table for that company.
            db.create_table(symbol)

            # Add entries for that table.
            db.add_stock_records(symbol, stock_data)

            logger.info("Load new company operation completed successfully.")
            return True, "OK"

    except ValueError as err:
        # ValueError indicates that passed symbol is invalid.
        logger.error("Symbol is invalid.")
        return False, str(err)
    except Exception as err:
        logger.error(err)


def convert_to_datetime(date):
    """Returns converted input date string into datetime object of format YYYY-MM-DD."""
    return datetime.strptime(date, '%Y-%m-%d')


def refresh_db():
    """This will load new available data if any for all stored companies from API to the database."""
    # Get last refreshed date for all companies.
    last_refresh_list = db.get_last_refresh()

    # Current timestamp
    today = datetime.now()

    # For each company stored locally check and load new data.
    for symbol, latest_refresh in last_refresh_list:
        last_refresh = convert_to_datetime(latest_refresh)

        # Check if not up-to-date.
        if today != last_refresh:
            # Get updated date from API for given symbol.
            update_date = apiHandler.get_refresh_date(symbol)

            # Check if update is available.
            if last_refresh < convert_to_datetime(update_date):
                # Update meta_data table
                db.update_refresh(symbol, update_date)

                # Fetch new data.
                stock_data = apiHandler.fetch_new_data(symbol, latest_refresh)

                # Add new data to database.
                db.add_stock_records(symbol, stock_data)


def fetch_record(symbol, date):
    """This will fetch a single day record for given company from local database.

    Args:
        symbol: (string) Company symbol.
        date: (string) Date of record to fetch.

    Returns:
            A boolean status of operation and related message.
            If operation is successfully it return True and (dictionary)stock data,
            False with appropriate error message otherwise.
    """
    today = datetime.now()
    if today < convert_to_datetime(date):                     # Check if a future date is passed.
        return False, "Can't get stock data for the future dates!"
    elif convert_to_datetime(date).weekday() > 4:             # Check if given date is a weekend.
        return False, "Its a weekend, market closed on this date."
    else:
        result = db.get_record(symbol, date)
        if result is None:                           # If no record for that date are found in local database.
            return False, "No records found for given date."
        else:
            # Write record to JSON file
            write_to_file(symbol, result)
            logger.info("Record fetch successfully.")
            return True, result


def get_trend(symbol):
    """This will return list of per date calculated trend(closing-opening) value for given company."""
    output = db.fetch_trend(symbol)
    logger.info("Trend calculation completed.")
    return output


def avg_trend(date):
    """This will calculate the average trend for a particular date using data of all available companies in database.

    Args:
        date: (string) Date for which average need to be calculated.

    Returns:
            A boolean status of operation and related message.
            If operation is successfully it return True and (float)average value,
            False with appropriate error message otherwise.
    """
    today = datetime.now()
    if today < convert_to_datetime(date):                     # Check if a future date is passed.
        return False, "Can't get stock data for the future dates!"
    elif convert_to_datetime(date).weekday() > 4:             # Check if given date is a weekend.
        return False, "Its a weekend, market closed on this date."
    else:
        result = db.comm_trend(date)
        if result is None:                                    # If database is empty.
            return False, "No company yet added."
        elif result is False:                                 # Missing record/weekday holiday.
            return False, "No records available for particular date."
        else:
            logger.info("Average of the date calculated.")
            return True, result


def trend_period(symbol):
    """This will calculate the maximum period of positive trend(closing-opening) for given company.

    Args:
        symbol: (string) symbol of company.

    Returns:
        3 values max positive period length, start date and end date for that period.
    """
    trend = db.fetch_trend(symbol)

    period = 0
    max_period = 0
    max_s = max_e = 0
    start = end = 0
    for rec in trend:
        if rec["trend"] > 0:
            if period == 0:
                start = end = rec["recorded_date"]
                period += 1
            else:
                end = rec["recorded_date"]
                period += 1
        else:
            if period > max_period:
                max_s = start
                max_e = end
                max_period = period

            start = end = period = 0

    logger.info("Positive trend period calculated successfully.")
    return max_period, max_s, max_e
