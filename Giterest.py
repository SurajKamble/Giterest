import gc
from flask import Flask, render_template, redirect, request, flash, session, url_for
from wtforms import Form, BooleanField, TextField, validators, PasswordField
from werkzeug.security import generate_password_hash, check_password_hash
from MySQLdb import escape_string
from connections import connection

app = Flask(__name__)
app.config['SECRET_KEY'] = 'Suraj' '''Used for security purpose in session encryption'''


class RegistrationForm(Form):
    username = TextField('Username', [validators.Length(min=4, max=20)])
    email = TextField('Email Address', [validators.Length(min=6, max=50), validators.email()])
    password = PasswordField('New Password',
                             [validators.Required(), validators.EqualTo('confirm', message='Passwords must match')])
    confirm = PasswordField('Repeat Password')


@app.route('/log_out/', methods=["GET", "POST"])
def log_out():
    if 'logged_in' in session:
        session.clear()
        flash("Logged out Successfully")
        return redirect(url_for('home'))
    return "Unauthorized Access"


@app.route('/home1/', methods=['GET', 'POST'])
def home1():
    if 'logged_in' in session:
        email = session['email']
        c, conn = connection()
        c.callproc('validate_login', (email,))

        data = c.fetchall()
        lat = data[0][4]
        lon = data[0][5]
        radius = 0.03
        c.close()
        if lat is not None and lon is not None:
            c, conn = connection()
            c.execute("SELECT * FROM user WHERE (latitude>=(%s) and latitude<=(%s)) and "
                      "(longitude>=(%s) and longitude<=(%s)) and(email!=(%s))", (lat-radius, lat+radius,
                                                                             lon-radius, lon+radius, email))
        users_nearby = c.fetchall()
        print users_nearby
        return render_template('index1.html', users_nearby=users_nearby)
    return redirect(url_for('home'))


@app.route('/', methods=["GET", "POST"])
def home():

    try:
        form = RegistrationForm(request.form)
        if 'logged_in' in session:
            return redirect(url_for('home1'))

    except Exception as e:
        return str(e)

    return render_template('home.html', form=form)


@app.route('/signUp/', methods=['GET', 'POST'])
def signUp():
    form = RegistrationForm(request.form)
    if request.method == "POST" and form.validate():
        username = escape_string(form.username.data)
        email = escape_string(form.email.data)
        password = generate_password_hash(form.password.data)
        c, conn = connection()
        print(password)
        c.callproc('createUser', (username, email, password))
        data = c.fetchall()
        if len(data) is 0:
            print "Success"
            conn.commit()
            flash("Thanks for registering, Welcome to Giterest")
            conn.close()
            gc.collect()
            session['logged_in'] = True
            session['email'] = email
            return redirect(url_for('select_tags'))
        else:
            print str(data)
            for d in data:
                flash(str(d[0]))
            return redirect(url_for('home'))
    return redirect(url_for('home'))

'''
Make a post request using js when the user allows to share their location.
Make one call to the database to get all the user's details and store it in a dict.
'''


@app.route('/select_tags/', methods=['GET', 'POST'])
def select_tags():
    if 'logged_in' in session and 'email' in session:
        c, conn = connection()
        c.execute("SELECT * from all_tags")
        tags_set = c.fetchall()
        print(type(tags_set))
        print(" Tags")
        print(tags_set)
        print(set(tags_set))

        tag_heads = []
        for tag_head in tags_set:
            tag_heads.append(tag_head[2])
        print "These are the tag_heads new: "
        tag_heads = set(tag_heads)
        print tag_heads
        tags = {}
        for tag_head in tag_heads:
            tags[tag_head] = []
            for tag in tags_set:
                if tag_head == tag[2]:
                    tags[tag_head].append([tag[0], tag[1]])

        tag_heads = tags.keys()
        print("These are the tags: ")
        print(tags)
        email = session['email']
        c.callproc('validate_login', (email,))
        data = c.fetchall()
        c.close()
        conn.commit()
        conn.close()
        user_id = data[0][0]
        lat = data[0][4]
        lon = data[0][5]
        print lat
        print lon
        if (lat is None and lon is None) or (lat == 0 and lon == 0):
            locationUpdated = False
        else:
            locationUpdated = True

        if request.method == 'POST':
            if not locationUpdated:
                lat = request.form['lat']
                lon = request.form['lon']
                print lat
                print lon
                c, conn = connection()
                c.callproc('updateLocation', (lat, lon, email))
                conn.commit()
                conn.close()
                gc.collect()
                locationUpdated = True

            select_tags1 = request.form['done_btn']
            print type(select_tags1)
            print select_tags1.split(',')
            x = []
            for tag in select_tags1.split(','):
                x.append(tag.encode('ascii'))
            print x
            add_tags(x, user_id)

        c, conn = connection()

        return render_template('select_tags.html', tags=tags, locationUpdated=locationUpdated)
    return "Unauthorized Access"


def add_tags(tags, user_id):
    c, conn = connection()
    for tag_id in tags:
        c.execute("INSERT INTO user_tags (user_id, tag_id) values ((%s), (%s))", (user_id, tag_id))
    conn.commit()
    conn.close()

'''
Convert all function calls to stored procedures.

'''


@app.route('/signin/', methods=['GET', 'POST'])
def signin_page():

    c, conn = connection()
    email = escape_string(request.form['emailsignin'])
    password = request.form['passwordsignin']
    c.callproc('validate_login', (email,))
    data = c.fetchall()
    print data
    if request.method == "POST" and len(data) > 0:

        if check_password_hash(str(data[0][3]), password):
            session['logged_in'] = True
            session['email'] = data[0][2]
            return redirect(url_for('home1'))

    flash("Invalid Email, Password combination")
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)

'''
      Droping a table with foreign keys
SET FOREIGN_KEY_CHECKS = 0; -- disable a foreign keys check
SET AUTOCOMMIT = 0; -- disable autocommit
START TRANSACTION; -- begin transaction

/*
DELETE FROM table_name;
ALTER TABLE table_name AUTO_INCREMENT = 1;
-- or
TRUNCATE table_name;
-- or
DROP TABLE table_name;
CREATE TABLE table_name ( ... );
*/

SET FOREIGN_KEY_CHECKS = 1; -- enable a foreign keys check
COMMIT;  -- make a commit


'''