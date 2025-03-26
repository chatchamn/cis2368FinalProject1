from flask import Flask, request, jsonify
import mysql.connector
from mysql.connector import Error
from datetime import datetime

app = Flask(__name__)

# Database connection setup
def create_connection():
    try:
        return mysql.connector.connect(
            host="cis2368.cvmow1hsmi4f.us-east-1.rds.amazonaws.com",
            user="admin",
            password="Cis2368!",
            database="FinalProject",
            connection_timeout=10

        )
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

# --- BOOK ROUTES ---

@app.route('/books', methods=['GET'])
def get_books():
    connection = create_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM books")
    books = cursor.fetchall()
    cursor.close()
    connection.close()
    return jsonify(books), 200

@app.route('/books/<int:book_id>', methods=['GET'])
def get_book_by_id(book_id):
    connection = create_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM books WHERE id = %s", (book_id,))
    book = cursor.fetchone()
    cursor.close()
    connection.close()
    if not book:
        return jsonify({'error': 'Book not found'}), 404
    return jsonify(book), 200

@app.route('/books', methods=['POST'])
def add_book():
    data = request.get_json()
    if not data or not all(k in data for k in ['title', 'author', 'genre']):
        return jsonify({'error': 'Missing required fields'}), 400
    connection = create_connection()
    cursor = connection.cursor()
    sql = "INSERT INTO books (title, author, genre) VALUES (%s, %s, %s)"
    cursor.execute(sql, (data['title'], data['author'], data['genre']))
    connection.commit()
    cursor.close()
    connection.close()
    return jsonify({'message': 'Book added successfully!'}), 201

@app.route('/books/<int:book_id>', methods=['PUT'])
def update_book(book_id):
    data = request.get_json()
    connection = create_connection()
    cursor = connection.cursor()
    sql = "UPDATE books SET title=%s, author=%s, genre=%s, status=%s WHERE id=%s"
    cursor.execute(sql, (
        data.get('title'), data.get('author'), data.get('genre'),
        data.get('status', 'available'), book_id))
    connection.commit()
    cursor.close()
    connection.close()
    return jsonify({'message': 'Book updated successfully!'}), 200

@app.route('/books/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM books WHERE id=%s", (book_id,))
    connection.commit()
    cursor.close()
    connection.close()
    return jsonify({'message': 'Book deleted successfully!'}), 200

# --- CUSTOMER ROUTES ---

@app.route('/customers', methods=['GET'])
def get_customers():
    connection = create_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT id, firstname, lastname, email FROM customers")
    customers = cursor.fetchall()
    cursor.close()
    connection.close()
    return jsonify(customers), 200

@app.route('/customers', methods=['POST'])
def add_customer():
    data = request.get_json()
    required = ['firstname', 'lastname', 'email', 'passwordhash']
    if not data or not all(field in data for field in required):
        return jsonify({'error': 'Missing fields'}), 400
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute("INSERT INTO customers (firstname, lastname, email, passwordhash) VALUES (%s, %s, %s, %s)",
                   (data['firstname'], data['lastname'], data['email'], data['passwordhash']))
    connection.commit()
    cursor.close()
    connection.close()
    return jsonify({'message': 'Customer added successfully'}), 201

# --- BORROWING ROUTES ---

@app.route('/borrowingrecords', methods=['POST'])
def create_borrowing():
    data = request.get_json()
    customer_id = data.get('customerid')
    book_id = data.get('bookid')
    borrow_date = data.get('borrowdate')

    if not customer_id or not book_id or not borrow_date:
        return jsonify({'error': 'Missing fields'}), 400

    connection = create_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("SELECT * FROM borrowingrecords WHERE customerid = %s AND returndate IS NULL", (customer_id,))
    if cursor.fetchone():
        return jsonify({'error': 'Customer already has a borrowed book'}), 400

    cursor.execute("SELECT status FROM books WHERE id = %s", (book_id,))
    book = cursor.fetchone()
    if not book or book['status'].lower() != 'available':
        return jsonify({'error': 'Book is not available'}), 400

    cursor.execute("INSERT INTO borrowingrecords (customerid, bookid, borrowdate, late_fee) VALUES (%s, %s, %s, 0.00)",
                   (customer_id, book_id, borrow_date))
    cursor.execute("UPDATE books SET status = 'unavailable' WHERE id = %s", (book_id,))
    connection.commit()
    cursor.close()
    connection.close()
    return jsonify({'message': 'Borrowing created successfully'}), 201

@app.route('/borrowingrecords/<int:borrowing_id>/return', methods=['PUT'])
def return_book(borrowing_id):
    data = request.get_json()
    return_date_str = data.get('returndate')
    if not return_date_str:
        return jsonify({'error': 'Missing returndate'}), 400

    try:
        return_date = datetime.strptime(return_date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

    connection = create_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM borrowingrecords WHERE id = %s", (borrowing_id,))
    borrowing = cursor.fetchone()
    if not borrowing:
        return jsonify({'error': 'Borrowing record not found'}), 404

    borrow_date = borrowing['borrowdate']
    book_id = borrowing['bookid']
    days_borrowed = (return_date - borrow_date).days
    late_fee = max(0, days_borrowed - 10)

    cursor.execute("UPDATE borrowingrecords SET returndate = %s, late_fee = %s WHERE id = %s",
                   (return_date, late_fee, borrowing_id))
    cursor.execute("UPDATE books SET status = 'available' WHERE id = %s", (book_id,))
    connection.commit()
    cursor.close()
    connection.close()
    return jsonify({'message': 'Book returned successfully', 'late_fee': late_fee}), 200

@app.route('/borrowingrecords', methods=['GET'])
def get_all_borrowings():
    connection = create_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("""
        SELECT br.id AS borrowing_id, c.firstname, c.lastname, b.title AS book_title,
               br.borrowdate, br.returndate, br.late_fee
        FROM borrowingrecords br
        JOIN customers c ON br.customerid = c.id
        JOIN books b ON br.bookid = b.id
        ORDER BY br.borrowdate DESC
    """)
    results = cursor.fetchall()
    cursor.close()
    connection.close()
    return jsonify(results), 200

# --- Run the app ---
if __name__ == '__main__':
    app.run(debug=True)