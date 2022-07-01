from flask import Flask  # From module flask import class Flask
app = Flask(__name__)    # Construct an instance of Flask class for our webapp

@app.route('/')   # URL '/' to be handled by main() route handler
def main():
    """Say hello"""
    return 'Hello, samim v1.0'

if __name__ == '__main__':  # Script executed directly?
    app.run(host='0.0.0.0',port=8080)  # Launch built-in web server and run this Flask webapp
