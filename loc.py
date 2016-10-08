from flask import Flask, request, render_template
import requests


app = Flask(__name__)


@app.route("/", methods=['GET', 'POST'])
def loc():
    if request.method == "POST":
        l = request.form['demo']
        l1 = request.form['demo1']
        print(l)
        print l1
        print "1"
    return render_template('loc.html')


@app.route("/a", methods=['GET', 'POST'])
def loc1():
    l = request.form['demo']
    l1 = request.form['demo1']
    print(l)
    print l1
    return l + l1

if __name__ == '__main__':
    app.run()
