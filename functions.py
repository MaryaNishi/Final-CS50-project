import requests
import sqlite3 
from config import cache
from flask import request
import re
from flask import redirect, render_template, session
from functools import wraps
from datetime import datetime

headers = {
            'User-Agent': 'Yummy Store/1.0.0 (marynishi2002@gmail.com)'
            }

def custom_cache_key1():
    query_string = request.query_string.decode('utf-8') or ''
    path = request.path
    endpoint = request.endpoint
    key = f"function1:{endpoint}:{path}:{query_string}"
    print(f"Generated cache key: {key}")
    return key

def custom_cache_key2():
    query_string = request.query_string.decode('utf-8') or ''
    path = request.path
    endpoint = request.endpoint
    key = f"function2:{endpoint}:{path}:{query_string}"
    print(f"Generated cache key: {key}")
    return key


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('user_id') is None:
            return redirect('/')
        return f(*args, **kwargs)
    return decorated_function


def modify_card(list):
    return ', '.join(list) + '.'

def get_nutriments(list):
    new_nutriments = {}

    desired_nutriments = {
        'Energy': ['energy-kcal_100g', 'kcal'],
        'Fat': ['fat_100g', 'g'],
        'Saturated fat': ['saturated-fat_100g', 'g'],
        'Carbohydrates': ['carbohydrates_100g', 'g'],
        'Sugars': ['sugars_100g', 'g'],
        'Fiber': ['fiber_100g', 'g'],
        'Proteins': ['proteins_100g', 'g'],
        'Salt': ['salt_100g', 'g'],
        'Fruits‚ vegetables‚ nuts and rapeseed‚ walnut and olive oils (estimate from ingredients list analysis)': ['fruits-vegetables-nuts-estimate-from-ingredients_100g', '%']
    }

    for key, value in desired_nutriments.items():
        new_nutriments[key] = str(list.get(value[0], 0)) + ' ' + value[1]

    return new_nutriments


def make_card(product={}, fields=''):

    card = {}
    fields = fields.split(',')

    for field in fields:
        if field != 'images':
            try:
                card[field] = product[field]
            except KeyError:
                print('KeyError in make_card function')
                return {}
    
    if not card['product_name']:
        print('Product name is missed in make_card function')
        return {}
    
    pattern = re.compile(r'/([^/]+)\.\d+\.\d+\.jpg$')

    match = pattern.search(card['image_url'])

    if not match:
        print('The picture is not found in make_card function')
        return {}

    key = match.group(1)

    img_dimension = product["images"][key]['sizes']['400']

    if img_dimension['w'] > img_dimension['h']:
        class_name = "fit-width"
    else:
        class_name = "fit-height"

    card['class_name'] = class_name
                
    return card


def get_products(sort=False, size=50, page=1, search_terms='', add_fields='', api_url='https://world.openfoodfacts.org/cgi/search.pl?'):

    fields = 'product_name,brands,quantity,code,images,image_url'

    if add_fields:
        fields = fields + ',' + add_fields
    
    params = {
    "search_terms": search_terms,
    "sort_by": "popularity" if sort else '',
    "fields": fields,
    "page_size": size,
    "page": page,
    "json": 1
    }

    response = requests.get(api_url, params=params, headers=headers)

    if not response.status_code == 200:
         print(f"Error in get_product function. Response status code: {response.status_code}")
         return render_template('error.html', error=500)
    
    data = response.json()
    
    if data.get('products'):
        products = data.get('products')

        overall_info = {}
        cards = []
        count = 0

        for product in products:
            card = make_card(product=product, fields=fields)

            if card:
                cards.append(card)
                count += 1

        overall_info = {
            'count': count,
            'cards': cards
        }

        return overall_info
    
    elif data.get('product'):
        product = data.get('product')
        card = make_card(product=product, fields=fields)
        return card
    else:
        print('Error in get_product function. Could not get information about products.')
        return render_template('error.html', error=500)


@cache.cached(timeout=31536000, key_prefix=custom_cache_key1)
def get_cached_cards():

    '''
    products = get_products(sort=True)
    print('cards done')
    return products['cards']
    '''
    size = 50
    page = 1
    cards = []
    count_cards = 0

    while True:
        products = get_products(size=size, page=page, sort=True)

        differ = size - count_cards
        cards.extend(products['cards'][:differ])

        count_cards += products['count'] if differ > products['count'] else differ

        if count_cards >= size:
            break

        page += 1
    
    return cards
    

def get_cards(url='https://world.openfoodfacts.org/cgi/search.pl?', search_terms='', id=''):
    if id:
        url = f'https://world.openfoodfacts.net/api/v2/product/{ id }?'
        product = get_products(api_url=url, add_fields='labels_tags_en,countries_tags_en,ingredients_tags_en,nutrient_levels_tags_en,nutriments')
        return product
    
    products = get_products(api_url=url, search_terms=search_terms)
    return products['cards']

def get_search_cards(search_term=''):
    size = 5
    page = 1
    cards = []
    count = 0

    while True:
        products = get_products(size=size, page=page, search_terms=search_term)

        differ = size - count
        cards.extend(products['cards'][:differ])

        count += products['count'] if differ > products['count'] else differ
        page += 1

        if count >= size:
            break
    
    return cards


@cache.cached(timeout=31536000, key_prefix=custom_cache_key2)
def get_cached_categories():

    url = 'https://world.openfoodfacts.org/categories.json'

    response = requests.get(url, headers=headers)

    if not response.status_code == 200:
         print(f"Error in get_cached_categories function. Response status code: {response.status_code}")
         return render_template('error.html', error=500)
    
    data = response.json()

    try:
        categories = data['tags']
        return categories

    except KeyError:
        print('Failed to retrieve categories in get_cached_categories function')
        return render_template('error.html', error=500)
 

def usd(value):
    return f"${value:,.2f}"


def get_date(datetime_str):
    dt_obj = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S.%f")
    
    formatted_date = dt_obj.strftime("%B %d, %Y at %H:%M")
    return formatted_date 