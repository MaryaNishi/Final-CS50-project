# Yummy. Online grocery store.
#### Video Demo:  <URL HERE>
#### Description:

**My project is a Yummy online grocery store.**


**General information:**
   Yummy is simply a website that allows you to buy some groceries.
   
   *There are several web pages such as*
   - main page with the top 50 popular products,
   - orders page where you can look at all of your completed orders
   - cart page where groceries are kept while you are searching for other products and where you can make your order
   - product page where you can look in detail about each product.
  
**Languages:**
  - *For backend* - python
  - *For frontend* - HTML, CSS, Javascript + Jinja
  - *For database* - sqlite3
  
**New features that were used:**
- In this project I have tried the free API (openfoodfacts). I have configured the API query, and I have learned how to get the information from there 
    after reading the API documentation.
- I also have tried some new features in python (try/except, and a lot of Javascript functions)
- I wrote all the code in Vs code so I've learned how to configure the code field, use sqlite3 and other features that I took for granted in the cloud CS50 version.


**Downside of API:**
- Free API from openfoodfacts is not perfect.
- First of all, for free usage I can only make 10 query per minute which is quite insufficient for making advanced quick search input (where you type the letter in and some suggestions appear immediately). This was the reason why my search input shows the results only when you click the search button.
- Secondly, the data in this API stores in some cases randomly (for example, I get the barcode of my product and then when I make a search via this code I get another   image or product_name).
- Thirdly, the images are not perfect, they sometimes do not look like they should be in the online grocery store.
- Sometimes queries are very slow
- And lastly, there are not any prices for items so I randomly chose a static price as 100$.


**Pros:**
- I have searched and tried many API but still the OpenFoodFacts was the best for my project. The main reason is that I can make infinite amounts of queres(in spite of the limit in 1 minute). Other APIs suggest only some certain limit for 1 month or so.
- Huge amount of items in the database with detailed information about each product.


**Lets dive into each page of the project.**
   **Functionality of each html page:**
   
   1. layout.html
      Layout.html is mostly a header with categories menu, search input and some information about the company.
      - 'YUMMY' button (left top corner) navigates to the main page.
      - 'About Company' and 'Contacts'(right top corner) give you the list of the information. The elements of the lists are not clickable.
      - Catalog button opens the menu with all categories which are generated via API query. Each element is clickable and shows about 50 products of a certain category.
      - Search input - type in the name of the product and click the search button. There will be the list of first 5 products, each of them you can click and go to the products.html for getting detailed information about the product. Moreover, you can click 'all results' to get all products with the name that you type in.
      - Login/Logout button helps you to register/login or logout(stop the session). All data is stored in the shop.db.
      - Orders and cart buttons navigate to corresponding page

    2. index.html
        - shows about 50 products that the user needs. The main page shows by default the first 50 products. Then when you click category or search in the input you can get other products. Each product is a card with an 'add to cart' button. Clicking to this button the product will be added to the cart and you will see the number of products in the cart near the cart button (for the beginning is 0). When you click to the cart, it navigates you to the products.html for detailed information.

    3. cart.html
        - shows products that user add via add to cart button (in index.html and products.html)
        - information is maintained during an active session. After logout the cart will be empty.
        - make an order button helps to make the order (add all necessary information into shop.db) and redirect to the orders.html

    4. orders.html
        - shows all recent orders that were made by the user. The information is stored in the shop.db.
    5. products.html
        - shows detailed information about the product. All information are from API (nutrients, where produced and so on)

    **Python code:**
    - I separated the python code into 2 files (app.py, fuctnions.py and config.py)
    - app.py is mostly the file for routes
    - functions.py - for functions that I used in app.py
    - config.py hepls me to configure the cache that I can use in functions.py and app.py.
