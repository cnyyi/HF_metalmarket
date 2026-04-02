from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello, Simple Test!'

if __name__ == '__main__':
    print("\n===== ALL ROUTES =====")
    for rule in app.url_map.iter_rules():
        print(f"{rule.rule} -> {rule.endpoint}")
    print("=====================\n")
    app.run(debug=True, port=5002)