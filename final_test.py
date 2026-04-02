from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello, World!'

@app.route('/test')
def test():
    return 'Hello, Test!'

@app.route('/user/list')
def user_list():
    return 'Hello, User List!'

@app.route('/merchant/list')
def merchant_list():
    return 'Hello, Merchant List!'

if __name__ == '__main__':
    print("\n===== ALL ROUTES =====")
    for rule in app.url_map.iter_rules():
        print(f"{rule.rule} -> {rule.endpoint}")
    print("=====================\n")
    app.run(debug=True, port=5003)