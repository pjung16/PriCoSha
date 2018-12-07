#Import Flask Library
from flask import Flask, render_template, request, session, url_for, redirect
import pymysql.cursors
import hashlib
import sys

#Initialize the app from Flask
app = Flask(__name__)

#Configure MySQL
conn = pymysql.connect(host='localhost',
                       port = 8889,
                       user='root',
                       password='root',
                       db='PriCoSha',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)

#Define a route to hello function
@app.route('/')
def hello():
    try:
        username = session['username']
        return redirect(url_for('home'))
    except:
        cursor = conn.cursor();
        query = 'SELECT item_id, email_post, post_time, item_name, file_path FROM ContentItem \
                 WHERE is_pub = 1 AND post_time >= NOW() - INTERVAL 1 DAY ORDER BY post_time DESC'
        cursor.execute(query)
        data = cursor.fetchall()
        cursor.close()
        return render_template('index.html', posts = data)

#Define route for login
@app.route('/login')
def login():
    try:
        username = session['username']
        return redirect(url_for('home'))
    except:
        return render_template('login.html')

#Define route for register
@app.route('/register')
def register():
    try:
        username = session['username']
        return redirect(url_for('home'))
    except:
        return render_template('register.html')

#Authenticates the login
@app.route('/loginAuth', methods=['GET', 'POST'])
def loginAuth():
    #grabs information from the forms
    try:
        username = session['username']
        return redirect(url_for('home'))
    except:
        username = request.form['username']
        password = hashlib.sha256(request.form['password'].encode('utf-8')).hexdigest()

        #cursor used to send queries
        cursor = conn.cursor()
        #executes query
        query = 'SELECT * FROM Person WHERE username = %s and password = %s'
        cursor.execute(query, (username, password))
        #stores the results in a variable
        data = cursor.fetchone()
        #use fetchall() if you are expecting more than 1 data row
        cursor.close()
        error = None
        if(data):
            #creates a session for the the user
            #session is a built in
            session['username'] = username
            return redirect(url_for('home'))
        else:
            #returns an error message to the html page
            error = 'Invalid login or username'
            return render_template('login.html', error=error)

#Authenticates the register
@app.route('/registerAuth', methods=['GET', 'POST'])
def registerAuth():
    #grabs information from the forms
    try:
        username = session['username']
        return redirect(url_for('home'))
    except:
        username = request.form['username']
        password = hashlib.sha256(request.form['password'].encode('utf-8')).hexdigest()
        fname = request.form['fname']
        lname = request.form['lname']

        #cursor used to send queries
        cursor = conn.cursor()
        #executes query
        query = 'SELECT * FROM Person WHERE username = %s'
        cursor.execute(query, (username))
        #stores the results in a variable
        data = cursor.fetchone()
        #use fetchall() if you are expecting more than 1 data row
        error = None
        if(data):
            #If the previous query returns data, then user exists
            error = "This user already exists"
            return render_template('register.html', error = error)
        else:
            ins = 'INSERT INTO Person VALUES(%s, %s, %s, %s)'
            cursor.execute(ins, (username, password, fname, lname))
            conn.commit()
            cursor.close()
            return render_template('index.html')


@app.route('/home')
def home():
    try:
        username = session['username']
        cursor = conn.cursor();
        query = 'SELECT item_id, email_post, post_time, item_name, file_path FROM ContentItem WHERE is_pub = 1 \
                UNION \
                SELECT item_id, email_post, post_time, item_name, file_path FROM ContentItem \
                WHERE item_id IN (SELECT item_id FROM Share WHERE fg_name IN (SELECT fg_name FROM Belong WHERE email = %s)) \
                ORDER BY post_time DESC'
        cursor.execute(query, (username))
        data = cursor.fetchall()
        query = 'SELECT fname FROM Person WHERE username = %s'
        cursor.execute(query, (username))
        name = cursor.fetchone()
        query = 'SELECT * FROM Belong WHERE email = %s'
        cursor.execute(query, (username))
        groups = cursor.fetchall()
        cursor.close()
        return render_template('home.html', username = name, posts = data, groups = groups)
    except:
        return redirect(url_for('hello'))

        
@app.route('/post', methods=['GET', 'POST'])
def post():
    try:
        username = session['username']
        cursor = conn.cursor();
        file_path = request.form['file_path']
        item_name = request.form['item_name']
        fg_name = request.form.getlist('fg_name')
        is_pub = 0
        if (request.form.get('is_pub')):
            is_pub = 1
        query = 'INSERT INTO ContentItem (email_post, file_path, item_name, is_pub) VALUES(%s, %s, %s, %s)'
        cursor.execute(query, (username, file_path, item_name, is_pub))
        conn.commit()
        item_id = cursor.lastrowid
        query = 'INSERT INTO Share Values (%s, %s, %s)'
        for name in fg_name:
            cursor.execute(query, (username, name, item_id))
            conn.commit()
        cursor.close()
        return redirect(url_for('home'))
    except:
        return redirect(url_for('hello'))

@app.route('/create_group')
def createGroup():
    try:
        username = session['username']
        return render_template('create_group.html')
    except:
        return redirect(url_for('hello'))

@app.route('/createFg', methods=['GET', 'POST'])
def createFg():
    #grabs information from the forms
    try:
        username = session['username']
        fg_name = request.form['fg_name']
        description = request.form.get('description')
        cursor = conn.cursor()
        query = 'SELECT fg_name, owner_email FROM Friendgroup WHERE fg_name = %s AND owner_email = %s'
        cursor.execute(query, (fg_name, username))
        data = cursor.fetchone()
        #use fetchall() if you are expecting more than 1 data row
        error = None
        if(data):
            #If the previous query returns data, then user exists
            error = "This friend group already exists"
            return render_template('create_group.html', error = error)
        else:
            ins = 'INSERT INTO Friendgroup VALUES(%s, %s, %s)'
            cursor.execute(ins, (username, fg_name, description))
            conn.commit()
            ins = 'INSERT INTO Belong Values(%s, %s, %s)'
            cursor.execute(ins, (username, username, fg_name))
            conn.commit()
            cursor.close()
            return redirect(url_for('home'))
    except:
        return redirect(url_for('hello'))

@app.route('/add_friend')
def addFriend():
    try:
        username = session['username']
        cursor = conn.cursor();
        query = 'SELECT * FROM Friendgroup WHERE owner_email = %s'
        cursor.execute(query, (username))
        groups = cursor.fetchall()
        return render_template('add_friend.html', groups = groups)
    except: 
        return redirect(url_for('hello'))

@app.route('/addToGroup', methods=['GET', 'POST'])
def addToGroup():
    try:
        username = session['username']
        fname = request.form['fname']
        lname = request.form['lname']
        fg_name = request.form.get('fg_name')
        cursor = conn.cursor()
        query = 'SELECT * FROM Person WHERE (fname = %s AND lname = %s) AND Person.username NOT IN (SELECT email FROM Belong WHERE fg_name = %s)'
        cursor.execute(query, (fname, lname, fg_name))
        people = cursor.fetchall()
        #use fetchall() if you are expecting more than 1 data row
        multiple = None
        error = None
        if (not people):
            return redirect(url_for('addToGroupError'))
        else:
            return render_template('add_friend_choose.html', people = people, fg_name = fg_name)
    except:
        return redirect(url_for('hello'))

@app.route('/add_friend_err')
def addToGroupError():
    try:
        username = session['username']
        cursor = conn.cursor();
        query = 'SELECT * FROM Friendgroup WHERE owner_email = %s'
        cursor.execute(query, (username))
        groups = cursor.fetchall()
        cursor.close()
        error = "Person is already in the friend group or does not exist"
        return render_template('add_friend.html', groups = groups, error = error)
    except:
        return redirect(url_for('hello'))

@app.route('/add_friend_choose')
def chooseFriend():
    try:
        username = session['username']
        return render_template('add_friend.html')
    except:
        return redirect(url_for('hello'))

@app.route('/addToGroupChoose', methods=['GET', 'POST'])
def addToGroupChoose():
    try:
        username = session['username']
        cursor = conn.cursor();
        email = request.form['email']
        fg_name = request.form['fg_name']
        ins = 'INSERT INTO Belong VALUES(%s, %s, %s)'
        cursor.execute(ins, (email, username, fg_name))
        conn.commit()
        cursor.close()
        return redirect(url_for('home'))
    except:
        return redirect(url_for('hello'))

@app.route('/content_item/<id_num>')
def viewContentItem(id_num):
    try:
        username = session['username']
        cursor = conn.cursor();
        query = 'SELECT * FROM ContentItem WHERE item_id = %s'
        cursor.execute(query, (id_num))
        content_item = cursor.fetchone()
        query = 'SELECT * FROM Rate WHERE item_id = %s'
        cursor.execute(query, (id_num))
        ratings = cursor.fetchall()
        query = 'SELECT * FROM Tag WHERE item_id = %s and status = 1'
        cursor.execute(query, (id_num))
        tags = cursor.fetchall()
        cursor.close()
        return render_template('content_item.html', id_num = id_num, item = content_item, ratings = ratings, tags = tags)
    except:
        return redirect(url_for('hello'))

@app.route('/content_item/<id_num>/tagFriend', methods=['GET', 'POST'])
def tagFriend(id_num):
    try:
        username = session['username']
        content_num = id_num
        tag_email = request.form['email']
        status = False
        query = 'SELECT item_id FROM ContentItem WHERE (is_pub = 1 AND item_id = %s)\
                 UNION SELECT item_id FROM ContentItem WHERE item_id IN (SELECT item_id \
                 FROM Share WHERE item_id = %s AND fg_name IN (SELECT fg_name FROM belong WHERE email = %s)); '
        cursor = conn.cursor()
        cursor.execute(query, (content_num, content_num, tag_email))
        can_view = cursor.fetchall()
        query = 'SELECT * FROM Tag WHERE email_tagged = %s AND email_tagger = %s AND item_id = %s'
        cursor.execute(query, (tag_email, username, id_num))
        duplicate = cursor.fetchall()
        print(tag_email, file=sys.stdout)
        print(username, file=sys.stdout)
        if (duplicate):
            error = "You already tagged this person in this post"
            return redirect(url_for('tagFriendError', error = error, id_num = content_num))
        elif (tag_email == username):
            status = True
            query = 'INSERT INTO Tag(email_tagged, email_tagger, item_id, status) VALUES(%s, %s, %s, %s)'
            cursor.execute(query, (tag_email, username, id_num, status))
            conn.commit()
            cursor.close()
            return redirect(url_for('viewContentItem', id_num = content_num))
        elif (can_view):
            query = 'INSERT INTO Tag(email_tagged, email_tagger, item_id, status) VALUES(%s, %s, %s, %s)'
            cursor.execute(query, (tag_email, username, id_num, status))
            conn.commit()
            cursor.close()
            return redirect(url_for('viewContentItem', id_num = content_num))
        else:
            error = "Person you're trying to tag can't view this post or doesn't exist"
            return redirect(url_for('tagFriendError', error = error, id_num = content_num))
    except:
        return redirect(url_for('hello'))

@app.route('/content_item/<id_num>/tagFriendErr')
def tagFriendError(id_num):
    try:
        username = session['username']
        error = request.args['error']
        cursor = conn.cursor();
        query = 'SELECT * FROM ContentItem WHERE item_id = %s'
        cursor.execute(query, (id_num))
        content_item = cursor.fetchone()
        query = 'SELECT * FROM Rate WHERE item_id = %s'
        cursor.execute(query, (id_num))
        ratings = cursor.fetchall()
        query = 'SELECT * FROM Tag WHERE item_id = %s and status = 1'
        cursor.execute(query, (id_num))
        tags = cursor.fetchall()
        cursor.close()
        return render_template('content_item.html', id_num = id_num, item = content_item, ratings = ratings, tags = tags, error = error)
    except:
        return redirect(url_for('hello'))

@app.route('/manage_tags')
def manageTags():
    try:
        username = session['username']
        cursor = conn.cursor();
        query = 'SELECT ContentItem.item_id, email_post, post_time, item_name, file_path, email_tagger, status FROM ContentItem NATURAL JOIN Tag\
                 WHERE (email_tagged, status) IN (SELECT email_tagged, status FROM Tag WHERE email_tagged = %s AND status = 0)'
        cursor.execute(query, (username))
        tags = cursor.fetchall()
        cursor.close()
        return render_template('manage_tags.html', tags = tags)
    except:
        return redirect(url_for('hello'))

@app.route('/acceptTag/<id_num>+<email_tagger>', methods=['GET', 'POST'])
def acceptTag(id_num, email_tagger):
    try:
        username = session['username']
        cursor = conn.cursor();
        query = 'UPDATE Tag SET status = 1 WHERE email_tagged = %s AND email_tagger = %s AND item_id = %s'
        cursor.execute(query, (username, email_tagger, id_num))
        conn.commit()
        cursor.close()
        return redirect(url_for('manageTags'))
    except:
        return redirect(url_for('hello'))

@app.route('/declineTag/<id_num>+<email_tagger>', methods=['GET', 'POST'])
def declineTag(id_num, email_tagger):
    try:
        username = session['username']
        cursor = conn.cursor();
        query = 'DELETE FROM Tag WHERE email_tagged = %s AND email_tagger = %s AND item_id = %s'
        cursor.execute(query, (username, email_tagger, id_num))
        conn.commit()
        cursor.close()
        return redirect(url_for('manageTags'))
    except:
        return redirect(url_for('hello'))

@app.route('/logout')
def logout():
    session.pop('username')
    return redirect('/')
        
app.secret_key = 'some key that you will never guess'
#Run the app on localhost port 5000
#debug = True -> you don't have to restart flask
#for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
    app.run('127.0.0.1', 5000, debug = True)
