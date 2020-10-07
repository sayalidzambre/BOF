import operations as op
import dbHandler as db
import flask
from flask import redirect, request, render_template, url_for, flash

import logging
from logging.config import fileConfig

# This will add only error message from werkzeug to log file.
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# Loading logger configurations
fileConfig('logger_config.ini')
logger = logging.getLogger()

app = flask.Flask(__name__)
app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245'


@app.route('/')
@app.route('/home')
def home():
    """Home page."""
    logger.info("Home page loaded.")
    return render_template("home.html")


@app.route("/loadStockData", methods=['GET', 'POST'])
def load():
    """Controls the load new company functionality of the app."""

    available_sym = db.get_companies()
    if request.method == 'GET':
        return render_template("NewCompany.html", available=available_sym)

    elif request.method == 'POST':
        symbol = request.form['symbol']
        status, msg = op.load_new_company(symbol)

        if status is False:
            if "Data" in msg:
                flash(msg, "info")
            else:
                flash(msg, "danger")
        else:
            flash("Data loaded successfully!", "success")

        return redirect(url_for('load'))


@app.route('/fetchStock', methods=['GET', 'POST'])
def fetch_stock():
    """Controls the single record fetch functionality of the app."""

    available_companies = db.get_companies()
    if request.method == 'POST':
        data = request.form
        status, output = op.fetch_record(data["symbol"], data["date"])

        if status is False:
            if "future" in output:
                flash(output, "warning")
            elif "closed" in output:
                flash(output, "info")
            elif "No" in output:
                flash(output, "danger")

            return redirect(url_for("fetch_stock"))

        else:
            flash("Data fetched successfully!", "success")
            return render_template("FetchRecords.html",
                                   symbols=available_companies, data=request.form, result=output,
                                   fetch=True)
    else:
        return render_template("FetchRecords.html", symbols=available_companies, fetch=False)


@app.route('/Stocktrend', methods=['GET', 'POST'])
def cal_trend():
    """Controls the Trend calculating functionality of the app."""

    available_companies = db.get_companies()
    if request.method == 'POST':
        data = request.form
        result = op.get_trend(data["symbol"])
        return render_template("trend.html",
                               symbols=available_companies, data=request.form, result=result,
                               fetch=True)
    else:
        return render_template("trend.html", symbols=available_companies, fetch=False)


@app.route('/Avgtrend', methods=['GET', 'POST'])
def cal_avgtrend():
    """Controls the Average trend calculation functionality of the app."""

    if request.method == 'POST':
        data = request.form
        status, output = op.avg_trend(data["date"])

        if status is False:
            if "future" in output:
                flash(output, "warning")
            elif "closed" in output:
                flash(output, "info")
            elif "company" in output:
                flash(output, "danger")
            elif "records" in output:
                flash(output, "danger")

            return redirect(url_for("cal_avgtrend"))
        else:
            flash("Average calculated successfully!", "success")
            return render_template("AverageTrend.html", data=request.form, result=output, fetch=True)
    else:
        return render_template("AverageTrend.html", fetch=False)


@app.route('/Positivetrend', methods=['GET', 'POST'])
def cal_postrend():
    """Controls the maximum positive trend period finder functionality of the app."""

    available_companies = db.get_companies()
    if request.method == 'POST':
        data = request.form
        result = op.trend_period(data["symbol"])
        return render_template("PositiveTrend.html",
                               symbols=available_companies, data=request.form, result=result,
                               fetch=True)
    else:
        return render_template("PositiveTrend.html", symbols=available_companies, fetch=False)


def refresh():
    """Every time the apps start this function will check for availability of new data
    and if any new updates are available it will load those entries into the database.
    This tried to ensure that app always displays latest possible information to user."""
    logger.info("Checking for new data.")
    op.refresh_db()


if __name__ == "__main__":
    # Load new data if available before starting the app.
    print("Loading....")
    # refresh()
    # logger.info("Database successfully refreshed.")

    logger.info("Starting app.")
    # Now that latest possible data is loaded into database, lets start the app.
    # app.run()

    app.run(debug=True)
