from flask import Flask, flash, redirect, render_template, request, session, jsonify, g
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from config import init_app, cache
from functions import usd, get_cached_cards, get_cached_categories, get_search_cards, get_cards, modify_card, get_nutriments, login_required, get_date
import sqlite3 
from sqlalchemy.exc import IntegrityError
from datetime import datetime


app = Flask(__name__)
init_app(app)

DATABASE = 'shop.db'


app.jinja_env.filters["usd"] = usd
app.jinja_env.filters["modify_card"] = modify_card
app.jinja_env.filters["get_nutriments"] = get_nutriments
app.jinja_env.filters["get_date"] = get_date

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)

    if db is not None:
        db.close()
    
    
@app.route("/", methods=["GET", "POST"])
def index():

    if request.method == 'POST':
        categories = get_cached_categories()
        if request.form.get('category'):
            q = request.form.get('category')
            cards = []
            for category in categories:
                try:
                    if q == category['id']:
                        general_name_products = category['name']
                        cards = get_cards(url=category['url'])
                        break
                except KeyError:
                    continue

            if not cards:
                print('There is no cards in the category in / route')
                return render_template('error.html', error=500)
            
            return render_template("index.html", cards=cards, categories=categories, general_name_products=general_name_products.capitalize(), 
                                   user_id=session.get('user_id'), cart=session.get('cart'))
        
        elif request.form.get('q'):
            q = request.form.get('q')
            cards = get_cards(search_terms=q)

            if not cards:
                print('There is no cards in the category in index()')
                return render_template('error.html', error=500)
            
            return render_template("index.html", cards=cards, categories=categories, general_name_products=q.capitalize(),
                                   user_id=session.get('user_id'), cart=session.get('cart'))
        else:
            print('There is no valid name for POST method in index()')
            return render_template('error.html', error=500)
        
    else:

        main_cards = get_cached_cards()
        categories = get_cached_categories()

        if not (main_cards and categories):
            print('Cards for main page or categories are missed.')
            return render_template('error.html', error=500)
    
        return render_template("index.html", cards=main_cards, categories=categories,  general_name_products='Popular products',
                               user_id=session.get('user_id'), cart=session.get('cart'))

@app.route("/products", methods=["GET", "POST"])
def products():
    
    id = request.args.get('card')
    if not id:
        print('There is no id for searching the product in /products')
        return render_template('error.html', error=404)
    
    card = get_cards(id=id)
    if not card:
        print('Desired product isnt found')
        return render_template('error.html', error=404)
    return render_template("products.html", categories = get_cached_categories(), card=card, user_id=session.get('user_id'),
                           cart=session.get('cart'))


@app.route("/orders", methods=["GET", "POST"])
def orders():

    db = get_db()

    purchases = []
    try: 
        query_distinct_date = ''' 
            SELECT DISTINCT date as date FROM orders WHERE user_id = ? ORDER BY date DESC
        '''

        cursor = db.execute(query_distinct_date, (session['user_id'], ))
        rows1 = cursor.fetchall()
        

        query_purchase = '''
            SELECT * FROM orders WHERE user_id = ? AND date = ?
        '''

        query_count_total = '''
            SELECT SUM(quantity * price) as total FROM orders WHERE user_id = ? AND date = ?
        '''

        for row1 in rows1:
            cursor = db.execute(query_purchase, (session['user_id'], row1['date']))
            rows2 = cursor.fetchall()

            cursor_total = db.execute(query_count_total, (session['user_id'], row1['date']))
            row_total = cursor_total.fetchone()
            total = row_total['total']

            cards = []

            for row2 in rows2:
                card = get_cards(id=row2['item_id'])
                if not card:
                    print('Desired products are not found')
                    return render_template('error.html', error=404)
                else:
                    card['count'] = row2['quantity']
                    card['price'] = row2['price']
                    cards.append(card)
                
            purchase = {
                        'cards': cards,
                        'date': row2['date'],
                        'total': total
                    }
            purchases.append(purchase)


    except Exception as e:
        print(f'An error occurred: {e}')

    return render_template('orders.html', categories = get_cached_categories(), purchases=purchases, user_id=session.get('user_id'),
                           cart=session.get('cart'))


   

@app.route("/search")
def search():
    q = request.args.get("q")
    if q:
        cards = get_search_cards(search_term=q)
    else:
        cards = []
    return cards

@app.route("/clear-cache")
def clead_cache():
    cache.clear()
    return render_template("error.html")

@app.route("/cart", methods=["GET", "POST"])
@login_required
def cart():
    cards = []

    unique_id = set(session['cart'])

    for id in unique_id:
        card = get_cards(id=id)
        if not card:
            print('Desired products are not found')
            return render_template('error.html', error=404)
        else:
            card['count'] = session['cart'].count(id)
            cards.append(card)

    return render_template("cart.html", categories = get_cached_categories(), cards=cards, user_id=session.get('user_id'),
                           cart=session.get('cart'), total_cart=len(session.get('cart')))
    
@app.route("/add_to_cart", methods=["POST"])
@login_required
def add_to_cart():
    data = request.json
    print(f'DATA IS {data}')

    session['cart'].append(data.get('item_id'))
    print(f'INSIDE: {session['cart']}')
    return jsonify(
        {"message": f"Item (id: {data.get('item_id')}) added to cart",
         "length": len(session['cart'])
         })

@app.route("/remove_from_cart", methods=["POST"])
@login_required
def remove_from_cart():
    data = request.json
    print(f'DATA IS {data}')

    if data.get('delete_all') ==  True:
        while (data.get('item_id') in session['cart']):
            session['cart'].remove(data.get('item_id'))
    else:
        session['cart'].remove(data.get('item_id'))

    print(f'AFTER: {session['cart']}')
    return jsonify(
        {"message": f"Item (id: {data.get('item_id')}) removed from cart",
         "length": len(session['cart'])
         })
    

@app.route("/make_order", methods=["POST"])
@login_required
def make_order():
   
    cards = []

    unique_id = set(session['cart'])
    for id in unique_id:
        card = {
            'item_id': id,
            'quantity': session['cart'].count(id)
        }
        cards.append(card)

    db = get_db()

    query = """
        INSERT INTO orders (user_id, item_id, quantity, price, date) VALUES (?, ?, ?, ?, ?)
    """
    
    current_time = datetime.now()
    try:

        with db:
            for card in cards:
                db.execute(query, (session['user_id'], card['item_id'], card['quantity'], 100, current_time))
                print('Item added to the orders list.')
        
            print('Order committed successfully.')

    except Exception as e:
        print(f'An error occurred: {e}')

    session['cart'].clear()
    return redirect('orders')

@app.route("/login", methods=["GET", "POST"])
def login():

    session.clear()
    cache.clear()

    if request.method == 'POST':
        if not (request.form.get('username') and request.form.get('password')):
                print('username or password are missed')
                return render_template('error.html', error='username or password are missed')
        
        username = request.form.get('username')
        password = request.form.get('password')

        db = get_db()
        try:
            query = """
                SELECT * FROM users WHERE username = ?
            """

            cursor = db.execute(query, (username, ))
            rows = cursor.fetchall()
        except sqlite3.IntegrityError:
            return render_template('error.html', error='Username does not exist, 400')

        if len(rows) != 1:
            print('The username does not exist')
            return render_template('error.html', error='The username does not exist')
        
        row = rows[0]

        if not check_password_hash(row['hash'], password):
            print('The password is not correct')
            return render_template('error.html', error='The password is not correct')

        session["user_id"] = row['id']
        session['cart'] = []

        return redirect("/")
    return redirect("/")


@app.route("/logout", methods=["GET", "POST"])
def logout():

    session.clear()

    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():

    session.clear()
    cache.clear()

    if request.method == 'POST':
        if not (request.form.get('username') and request.form.get('password') and request.form.get('password-confirmation')):
                print('username or passwords are missed')
                return render_template('error.html', error='username or passwords are missed')
        
        username = request.form.get('username')
        password = request.form.get('password')
        confirmation = request.form.get('password-confirmation')

        if password != confirmation:
            print('Passwords are different')
            return render_template('error.html', error='Passwords are different')
        
        hashed_password = generate_password_hash(password)

        db = get_db()
        try:

            query = """
                INSERT INTO users (username, hash) VALUES (?, ?)
            """
            with db:
                db.execute(query, (username, hashed_password))
            print('User registered successfully!')

        except sqlite3.IntegrityError:
            return render_template('error.html', error='Username already exists, 400')
        
        try:
            query = """
                    SELECT * FROM users WHERE username = ?
                """
            cursor = db.execute(query, (username, ))
            rows = cursor.fetchall()
        except sqlite3.IntegrityError:
            return render_template('error.html', error='Username does not exists, 400')

        if rows:
            row = rows[0] 
            session["user_id"] = row['id']
            session['cart'] = []

        return redirect('/')

    return redirect('/')

@app.route("/error")
def error():
    return render_template("error.html", error='lafknl')



