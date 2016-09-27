from app import app
from flask import request, jsonify
from utils import *

IN_PREFIX = "INBOUND_"
OUT_PREFIX = "OUTBOUND_"
SMS_LIMIT = 50
HOUR = 3600


@app.route('/inbound/sms/', methods=['POST'])
def inbound():

    try:
        # check and validate all the input
        error = validate_input(request.form)
        if error:
            return jsonify(error=error, message="")

        to_number = request.form["to"]
        text = request.form["text"]
        from_number = request.form["from"]

        # authenticate the request
        error = authenticate_account(request.form, to_number)
        if error:
            error %= "to"
            return jsonify(error=error, message="")

        # check if stop request was raised and set same in redis
        register_stop_request(text, IN_PREFIX + from_number, to_number, 4 * HOUR)

        # all is well
        error = ""
        message = "inbound sms ok"
        return jsonify(error=error, message=message)

    except exceptions.Forbidden as e:
        raise e
    except Exception as e:
        print e
        error = "unknown failure"
        return jsonify(error=error, message="")


@app.route('/outbound/sms/', methods=['POST'])
def outbound():
    try:
        # check and validates all the input
        error = validate_input(request.form)
        if error:
            return jsonify(error=error, message="")

        from_number = request.form["from"]
        to_number = request.form["to"]

        # authenticate the request
        error = authenticate_account(request.form, from_number)
        if error:
            error %= "from"
            return jsonify(error=error, message="")

        # check if stop request is registered in redis
        error = check_stop_request(IN_PREFIX + to_number, from_number)
        if error:
            error %= (from_number, to_number)
            return jsonify(error=error, meessage="")

        # check if usage limit has been crossed
        error = check_and_update_usage(OUT_PREFIX + from_number, SMS_LIMIT, 24*HOUR)
        if error:
            error %= from_number
            return jsonify(error=error, message="")

        # all is well
        message = "outbound sms ok"
        return jsonify(error="", message=message)

    except exceptions.Forbidden as e:
        raise e
    except Exception as e:
        print e
        return jsonify(error="unknown failure", message="")
