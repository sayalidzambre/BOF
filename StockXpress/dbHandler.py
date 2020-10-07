import mysql.connector
from mysql.connector import Error

import logging
from logging.config import fileConfig

# This will add only error message from werkzeug to log file.
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# Loading logger configurations
fileConfig('logger_config.ini')
logger = logging.getLogger()

# Database connection config parameters:
__dbhost__ = "localhost"
__dbname__ = "test_db"
__username__ = "root"


def create_connection():
    """This will create connection with MySQL Server database specified by __dbname__.

    Returns:
        Connection object.
    """
    try:
        conn = mysql.connector.connect(host=__dbhost__, database=__dbname__, user=__username__)
        if conn.is_connected():
            return conn
    except Error as e:
        logger.error("{}".format(e))


def create_table(name):
    """This will create new table with name of company symbol in local database.

    Args:
        name: (string) symbol of company.

    Returns:
        True if table created successfully, false otherwise.
    """
    try:
        conn = create_connection()
        cursor = conn.cursor()

        query = "CREATE TABLE {}(\
                    recorded_date DATE PRIMARY KEY,\
                    open DOUBLE(10,4) NOT NULL,\
                    high DOUBLE(10,4) NOT NULL,\
                    low DOUBLE(10,4) NOT NULL,\
                    close DOUBLE(10,4) NOT NULL,\
                    adjusted_close DOUBLE(10,4) NOT NULL,\
                    volume int NOT NULL,\
                    dividend_amount DOUBLE(6,4) NOT NULL,\
                    split_coefficient DOUBLE(6,4) NOT NULL\
                    );".format(name)

        cursor.execute(query)
        conn.commit()
        logger.info("Table for {} created.".format(name))
        return True

    except Exception as e:
        logger.error(e)
        return False
    finally:
        # closing database connection.
        if conn.is_connected():
            cursor.close()
            conn.close()


def add_company_data(symbol, refresh_date):
    """Adds new company details to Company_meta_data table.

    Args:
        symbol: (string) Symbol of the company.
        refresh_date: (string) last data refreshed date.

    Returns:
        True if record added successfully, false otherwise.
    """
    try:
        conn = create_connection()
        cursor = conn.cursor()

        query = "INSERT INTO Company_meta_data(symbol, last_refreshed) " \
                "VALUES('{}', '{}');".format(symbol, refresh_date)

        cursor.execute(query)
        # logger.debug("{} entries added to company_meta_data.".format(cursor.rowcount))
        conn.commit()

    except Exception as e:
        logger.error(e)
        return False
    finally:
        # closing database connection.
        if conn.is_connected():
            cursor.close()
            conn.close()


def add_stock_records(symbol, stock_data):
    """Adds stock data(all 8 factors and date) to respective company table in database.

    Args:
        symbol: (string) symbol of the company.
        stock_data: List of tuples of records to be added.

    Returns:
        True if records added successfully, false otherwise.
    """
    try:
        conn = create_connection()
        cursor = conn.cursor()

        query = "INSERT INTO {} values(%s, %s, %s, %s, %s, %s, %s, %s, %s);".format(symbol)
        cursor.executemany(query, stock_data)
        logger.info("{} entries inserted in {} table.".format(cursor.rowcount, symbol))
        conn.commit()

    except Exception as e:
        logger.error(e)
        return False
    finally:
        # closing database connection.
        if conn.is_connected():
            cursor.close()
            conn.close()


def get_companies():
    """Returns list of symbols of all companies whose stock data is available."""
    try:
        conn = create_connection()
        cursor = conn.cursor()

        query = "SELECT symbol FROM Company_meta_data;"
        cursor.execute(query)
        result = cursor.fetchall()

        # Create list of first tuple (symbols) obtained from the sql query result.
        available_companies = [sym[0] for sym in result]
        return available_companies

    except Exception as e:
        logger.error(e)
        return False
    finally:
        # closing database connection.
        if conn.is_connected():
            cursor.close()
            conn.close()


def get_last_refresh():
    """Returns list of (symbol,last refresh date) for each stored company."""
    try:
        conn = create_connection()
        cursor = conn.cursor()

        query = "SELECT symbol,last_refreshed FROM Company_meta_data;"
        cursor.execute(query)
        result = cursor.fetchall()
        return result

    except Exception as e:
        logger.error(e)
        return False
    finally:
        # closing database connection.
        if conn.is_connected():
            cursor.close()
            conn.close()


def update_refresh(symbol, new_date):
    """This will update the company_meta_data table with new refreshed dates.

    Args:
        symbol: (string) symbol of company to update.
        new_date: (string) new refreshed date.

    Returns:
        None.
    """
    try:
        conn = create_connection()
        cursor = conn.cursor()

        query = "UPDATE Company_meta_data " \
                "SET last_refreshed = '{}' " \
                "WHERE symbol='{}';".format(new_date, symbol)

        cursor.execute(query)
        conn.commit()

    except Exception as e:
        logger.error(e)
        return False
    finally:
        # closing database connection.
        if conn.is_connected():
            cursor.close()
            conn.close()


def get_record(symbol, date):
    """This will fetch a single day record for given company from database.

    Args:
        symbol: (string)  symbol of company.
        date: (string) date for which record needs to be fetched.

    Returns:
        Dictionary of requested record, else None.
    """
    try:
        conn = create_connection()
        cursor = conn.cursor(dictionary=True)

        query = "SELECT * FROM {} WHERE recorded_date='{}';".format(symbol, date)
        cursor.execute(query)
        result = cursor.fetchone()
        return result

    except Exception as e:
        logger.error(e)
        return False
    finally:
        # closing database connection.
        if conn.is_connected():
            cursor.close()
            conn.close()


def fetch_trend(symbol):
    """This will calculate and fetch per day trend for given company from the database.

    Args:
        symbol: (string) symbol of company.

    Returns:
        dictionary list of fetched records from database.
    """
    try:
        conn = create_connection()
        cursor = conn.cursor(dictionary=True)

        query = "SELECT recorded_date, (close-open) AS trend FROM {} ORDER BY recorded_date DESC;".format(symbol)
        cursor.execute(query)
        result = cursor.fetchall()

        return result

    except Exception as e:
        logger.error(e)
        return False
    finally:
        # closing database connection.
        if conn.is_connected():
            cursor.close()
            conn.close()


def comm_trend(date):
    """This will calculate the average trend(closing-opening) for given date using all available companies in database.

    Args:
        date: (string) date where average needs to be calculated.

    Returns:
        Calculated average value. For no companies in database
    """
    try:
        conn = create_connection()
        cursor = conn.cursor()

        company = get_companies()
        if company is None:      # if database is still empty.
            return None

        total = 0
        for sym in company:
            query = "SELECT (close-open) AS trend FROM {} WHERE recorded_date='{}';".format(sym, date)
            cursor.execute(query)
            result = cursor.fetchone()
            total += float(result[0])

        # Average calculation
        avg = total / len(company)
        return "{0:.4f}".format(avg)

    except Exception as e:
        logger.error(e)
        return False
    finally:
        # closing database connection.
        if conn.is_connected():
            cursor.close()
            conn.close()
