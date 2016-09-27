# plivo

## Setup

1. clone from github(https://github.com/manish2382/plivo.git) repository.
2. cd plivo
3. pip install -r requirement.txt
4. modify app/config.py to point to correct redis and postgres server.

## run
1. cd plivo
2. python run.py (this will start server @localhost:5000)


## testing
1. Modify app_tests.py => setup() function to point to test db and test redis server(by default it takes local redis running at 6379)
2. cd plivo
3. python app_tests.py
