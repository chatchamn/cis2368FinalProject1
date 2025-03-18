from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Database connection
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://admin:Cis2368%21@cis2368.cvmow1hsmi4f.us-east-1.rds.amazonaws.com:3306/FinalProject'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Models
class Book(db.Model):
    __tablename__ = 'books'  # Ensuring correct table name
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(200), nullable=False)
    genre = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='available')  # available/unavailable

class Customer(db.Model):
    __tablename__ = 'customers'  # Correct table name
    id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(100), nullable=False)
    lastname = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    passwordhash = db.Column(db.String(256), nullable=False)  # Store hashed passwords

class BorrowingRecord(db.Model):
    __tablename__ = 'borrowingrecords'
    id = db.Column(db.Integer, primary_key=True)
    bookid = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    customerid = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    borrowdate = db.Column(db.DateTime, default=datetime.utcnow)
    returndate = db.Column(db.DateTime, nullable=True)
    late_fee = db.Column(db.Float, default=0.0)

# Create tables if they do not exist
with app.app_context():
    db.create_all()

# CRUD Operations for Books
@app.route('/books', methods=['GET'])
def get_books():
    books = Book.query.all()
    return jsonify([{
        'id': book.id, 'title': book.title, 
        'author': book.author, 'genre': book.genre, 
        'status': book.status
    } for book in books])

@app.route('/books', methods=['POST'])
def add_book():
    try:
        data = request.get_json()
        if not data or not all(key in data for key in ['title', 'author', 'genre']):
            return jsonify({'error': 'Missing required fields'}), 400

        new_book = Book(title=data['title'], author=data['author'], genre=data['genre'])
        db.session.add(new_book)
        db.session.commit()
        return jsonify({'message': 'Book added successfully!'}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/books/<int:book_id>', methods=['PUT'])
def update_book(book_id):
    book = Book.query.get(book_id)
    if not book:
        return jsonify({'error': 'Book not found'}), 404

    data = request.get_json()
    book.title = data.get('title', book.title)
    book.author = data.get('author', book.author)
    book.genre = data.get('genre', book.genre)
    book.status = data.get('status', book.status)

    db.session.commit()
    
    return jsonify({'message': 'Book updated successfully!'})

@app.route('/books/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    book = Book.query.get(book_id)
    if not book:
        return jsonify({'error': 'Book not found'}), 404

    db.session.delete(book)
    db.session.commit()
    return jsonify({'message': 'Book deleted successfully!'})

# Run Flask app
if __name__ == '__main__':
    app.run(debug=True)