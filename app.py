from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime

app = Flask(__name__)

# Konfigurasi MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['library']
books_collection = db['books']
categories_collection = db['categories']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    categories = categories_collection.find()
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        category_id = request.form['category']
        publisher = request.form['publisher']
        release_date = request.form['release_date']
        number_of_pages = request.form['number_of_pages']
        
        book = {
            'title': title,
            'author': author,
            'category_id': ObjectId(category_id),
            'publisher': publisher,
            'release_date': release_date,
            'number_of_pages': number_of_pages
        }
        
        books_collection.insert_one(book)
        return redirect(url_for('list_books'))
    
    return render_template('add_book.html', categories=categories)

@app.route('/list_books')
def list_books():
    books = books_collection.aggregate([
        {
            '$lookup': {
                'from': 'categories',
                'localField': 'category_id',
                'foreignField': '_id',
                'as': 'category'
            }
        },
        {
            '$unwind': '$category'
        }
    ])
    return render_template('list_books.html', books=books)

@app.route('/view_all_books', methods=['GET', 'POST'])
def view_all_books():
    categories = categories_collection.find()
    selected_category_id = request.form.get('category_id')
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    search_text = request.form.get('search_text', '')

    query = {}

    if selected_category_id:
        query['category_id'] = ObjectId(selected_category_id)

    if start_date:
        query['release_date'] = {'$gte': start_date}
    
    if end_date:
        if 'release_date' in query:
            query['release_date']['$lte'] = end_date
        else:
            query['release_date'] = {'$lte': end_date}
    
    if search_text:
        query['$or'] = [
            {'title': {'$regex': search_text, '$options': 'i'}},
            {'author': {'$regex': search_text, '$options': 'i'}},
            {'publisher': {'$regex': search_text, '$options': 'i'}}
        ]
    
    books = books_collection.aggregate([
        {
            '$match': query
        },
        {
            '$lookup': {
                'from': 'categories',
                'localField': 'category_id',
                'foreignField': '_id',
                'as': 'category'
            }
        },
        {
            '$unwind': '$category'
        }
    ])
    
    return render_template('view_all_books.html', books=books, categories=categories, selected_category_id=selected_category_id, start_date=start_date, end_date=end_date, search_text=search_text)

@app.route('/edit_book/<id>', methods=['GET', 'POST'])
def edit_book(id):
    book = books_collection.find_one({'_id': ObjectId(id)})
    categories = categories_collection.find()
    if request.method == 'POST':
        updated_book = {
            'title': request.form['title'],
            'author': request.form['author'],
            'category_id': ObjectId(request.form['category']),
            'publisher': request.form['publisher'],
            'release_date': request.form['release_date'],
            'number_of_pages': request.form['number_of_pages']
        }
        books_collection.update_one({'_id': ObjectId(id)}, {'$set': updated_book})
        return redirect(url_for('list_books'))
    return render_template('edit_book.html', book=book, categories=categories)

@app.route('/delete_book/<id>', methods=['POST'])
def delete_book(id):
    books_collection.delete_one({'_id': ObjectId(id)})
    return redirect(url_for('list_books'))

@app.route('/add_category', methods=['GET', 'POST'])
def add_category():
    if request.method == 'POST':
        category_name = request.form['category_name']
        category = {'name': category_name}
        categories_collection.insert_one(category)
        return redirect(url_for('list_categories'))
    return render_template('add_category.html')

@app.route('/list_categories')
def list_categories():
    categories = categories_collection.find()
    return render_template('list_categories.html', categories=categories)

@app.route('/edit_category/<id>', methods=['GET', 'POST'])
def edit_category(id):
    category = categories_collection.find_one({'_id': ObjectId(id)})
    if request.method == 'POST':
        updated_category = {
            'name': request.form['category_name']
        }
        categories_collection.update_one({'_id': ObjectId(id)}, {'$set': updated_category})
        return redirect(url_for('list_categories'))
    return render_template('edit_category.html', category=category)

@app.route('/delete_category/<id>', methods=['POST'])
def delete_category(id):
    categories_collection.delete_one({'_id': ObjectId(id)})
    return redirect(url_for('list_categories'))

if __name__ == '__main__':
    app.run(debug=True)
