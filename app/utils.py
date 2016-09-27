import redis
from werkzeug import exceptions

from models import Account, phone_number
from config import REDIS_HOST, REDIS_PORT


def get_redis_connection():

    """
    Returns redis connection
    :return:
    """
    return redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=0)


def register_stop_request(text, key, value, expiry):

    """
    Checks for input text if it matches with STOP than register the key values pair for expiry interval
    :param text: incoming text
    :param key: key which will be registered
    :param value: value to be registered
    :param expiry: expiry in seconds
    :return: No return
    """
    if text.strip() == "STOP":
        r = get_redis_connection()

        # set expiry time as 4 hours
        r.set(key, value, ex=expiry)


def check_stop_request(key, from_number):

    """
    Check if key and from_number has been registered for stop request and raise error
    :param key: key value
    :param from_number:
    :return: error statement if stop request is registered else none
    """

    # check if stop request is registered in redis
    error = None
    r = get_redis_connection()
    if r.get(key) == from_number:
        error = "sms from %s to %s blocked by STOP request"

    return error


def authenticate_account(request, number):

    """
    Authenticates the account and raises error
    :param request: contains input parameter
    :param number: number belonging to some account
    :return: Error in case authentication fails
    """

    error = None
    username = request.get('username', None)
    auth_id = request.get('password', None)

    # authenticate the request
    account_obj = Account.query.filter_by(auth_id=auth_id, username=username).first()
    if not account_obj:
        raise exceptions.Forbidden()

    # check if number belongs to the particular account
    number_object = phone_number.query.filter_by(number=number, account_id=account_obj.id).first()
    if not number_object:
        error = "%s parameter not found"

    return error


def validate_input(request):

    """
    Checks for mandatory parameters and  validates each parameter
    :param request: contains the request data
    :return: it returns error if any otherwise it returns an account object
    """

    # Get all the mandatory parameter from request
    from_number = request.get('from', None)
    to_number = request.get('to', None)
    text = request.get('text', None)

    result = None
    # check if all the parameters are present
    error = "parameter '%s' is missing"
    if not from_number:
        result = error % "from"
    if not to_number:
        result = error % "to"
    if not text:
        result = error % "text"

    # return error message if any parameter is missing
    if result:
        return result

    # check validity of each input
    error = "parameter '%s' is invalid"
    if not (6 <= len(from_number) <= 16):
        result = error % "from"
    if not (6 <= len(to_number) <= 16):
        result = error % "to"
    if not (1 <= len(text) <= 120):
        result = error % "text"

    return result


def check_and_update_usage(key, limit, timeout):

    """
    Checks for usage limit and raises error if limit is crossed.
    Updates the usage count as well as remaining time after which usage counter will be reset
    :param key: number that is being used for sending out smses
    :param limit: from same number this api can be invoked till limit after that error will be raised
    :param timeout: seconds after which counter will be reset
    :return: Error statement if usage limit has been crossed
    """

    redis_conn = get_redis_connection()

    # lock the section so that multiple simultaneous request get correct count
    lock = redis_conn.lock("OUTBOUND", sleep=0.1, thread_local=True, timeout=10)
    # critical section starts
    lock.acquire()

    # check if the limit has crossed in last 24 hours
    count = redis_conn.get(key)

    if not count:
        # for expired/first time set expiry as 24 hours and count as 1
        redis_conn.set(key, 1, timeout)
    else:
        count = int(count)
        if count >= limit:
            return "limit reached for from %s"
        else:
            # increment the count and set the expiry timer to previous value
            ttl = redis_conn.pttl(key)
            redis_conn.psetex(key, ttl, count + 1)

    # critical section over
    lock.release()

    return None



