from flask import Flask
app = Flask(__name__)


@app.route('/')
def hello():
    i = 1
    i += 1
    return "Hello!!!"
    
@app.route('/pg2')
def hello_again():
    return "hello again!"

if __name__ == '__main__':
    app.run(debug=True)