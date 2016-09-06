import os
from flask import Flask

app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])

@app.route('/')
def hello():
    i = 1
    i += 1
    i += 5
    x = (os.environ['APP_SETTINGS'])    

    return "Hello!!! %s" %x
    
@app.route('/pg2')
def hello_again():
    return "hello again!"

if __name__ == '__main__':
    app.run(debug=True)