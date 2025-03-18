from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
CORS(app)

# Database connection 
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://admin:Cis2368%21@cis2368.cvmow1hsmi4f.us-east-1.rds.amazonaws.com:3306/FinalProject'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Models
class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(200), nullable=False)
    genre = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='available')  # available or unavailable

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(100), nullable=False)
    lastname = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    passwordhash = db.Column(db.String(256), nullable=False)

class BorrowingRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bookid = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    customerid = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    borrowdate = db.Column(db.DateTime, default=datetime.utcnow)
    returndate = db.Column(db.DateTime, nullable=True)
    late_fee = db.Column(db.Float, default=0.0)

# Create database tables
with app.app_context():
    db.create_all()

# CRUD Routes for Books
@app.route('/books', methods=['GET'])
def get_books():
    books = Book.query.all()
    return jsonify([{'id': b.id, 'title': b.title, 'author': b.author, 'genre': b.genre, 'status': b.status} for b in books])

@app.route('/books', methods=['POST'])
def add_book():
    data = request.json
    new_book = Book(title=data['title'], author=data['author'], genre=data['genre'])
    db.session.add(new_book)
    db.session.commit()
    return jsonify({'message': 'Book added successfully!'}), 201

@app.route('/books/<int:book_id>', methods=['PUT'])
def update_book(book_id):
    book = Book.query.get(book_id)
    if not book:
        return jsonify({'message': 'Book not found'}), 404
    data = request.json
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
        return jsonify({'message': 'Book not found'}), 404
    db.session.delete(book)
    db.session.commit()
    return jsonify({'message': 'Book deleted successfully!'})

# Run Flask
if __name__ == '__main__':
    app.run(debug=True)
