from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
    return 'Hello, Index!'

@app.route('/test1')
def test1():
    return 'Hello, Test1!'

@app.route('/test2')
def test2():
    return 'Hello, Test2!'

if __name__ == '__main__':
    print("\n===== ALL ROUTES =====")
    for rule in app.url_map.iter_rules():
        print(f"{rule.rule} -> {rule.endpoint}")
    print("=====================\n")
    app.run(debug=True, port=5001)