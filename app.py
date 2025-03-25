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
            database="FinalProject"
        )
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

# --- BOOK ROUTES ---

@app.route('/books', methods=['GET'])
def get_books():
    connection = create_connection()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM books")
    books = cursor.fetchall()
    cursor.close()
    connection.close()
    return jsonify(books), 200

@app.route('/books', methods=['POST'])
def add_book():
    data = request.get_json()
    if not data or not all(k in data for k in ['title', 'author', 'genre']):
        return jsonify({'error': 'Missing required fields'}), 400
    connection = create_connection()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500
    cursor = connection.cursor()
    sql = "INSERT INTO books (title, author, genre) VALUES (%s, %s, %s)"
    values = (data['title'], data['author'], data['genre'])
    cursor.execute(sql, values)
    connection.commit()
    cursor.close()
    connection.close()
    return jsonify({'message': 'Book added successfully!'}), 201

@app.route('/books/<int:book_id>', methods=['PUT'])
def update_book(book_id):
    data = request.get_json()
    connection = create_connection()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500
    cursor = connection.cursor()
    sql = "UPDATE books SET title=%s, author=%s, genre=%s, status=%s WHERE id=%s"
    values = (
        data.get('title'),
        data.get('author'),
        data.get('genre'),
        data.get('status', 'available'),
        book_id
    )
    cursor.execute(sql, values)
    connection.commit()
    cursor.close()
    connection.close()
    return jsonify({'message': 'Book updated successfully!'}), 200

@app.route('/books/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    connection = create_connection()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500
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
    cursor.execute("SELECT id, name, email FROM customers")
    customers = cursor.fetchall()
    cursor.close()
    connection.close()
    return jsonify(customers), 200

@app.route('/customers', methods=['POST'])
def add_customer():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')  # Stored as plain text
    if not name or not email or not password:
        return jsonify({'error': 'Missing fields'}), 400
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute("INSERT INTO customers (name, email, password) VALUES (%s, %s, %s)", (name, email, password))
    connection.commit()
    cursor.close()
    connection.close()
    return jsonify({'message': 'Customer added successfully'}), 201

@app.route('/customers/<int:customer_id>', methods=['PUT'])
def update_customer(customer_id):
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')  # Optional
    connection = create_connection()
    cursor = connection.cursor()
    if password:
        cursor.execute(
            "UPDATE customers SET name=%s, email=%s, password=%s WHERE id=%s",
            (name, email, password, customer_id)
        )
    else:
        cursor.execute(
            "UPDATE customers SET name=%s, email=%s WHERE id=%s",
            (name, email, customer_id)
        )
    connection.commit()
    cursor.close()
    connection.close()
    return jsonify({'message': 'Customer updated successfully'}), 200

@app.route('/customers/<int:customer_id>', methods=['DELETE'])
def delete_customer(customer_id):
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM customers WHERE id=%s", (customer_id,))
    connection.commit()
    cursor.close()
    connection.close()
    return jsonify({'message': 'Customer deleted successfully'}), 200

# --- BORROWING ROUTES ---

@app.route('/borrowings', methods=['POST'])
def create_borrowing():
    data = request.get_json()
    customer_id = data.get('customer_id')
    book_id = data.get('book_id')
    borrow_date = data.get('borrow_date')
    if not customer_id or not book_id or not borrow_date:
        return jsonify({'error': 'Missing fields'}), 400
    connection = create_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("SELECT * FROM borrowings WHERE customer_id = %s AND return_date IS NULL", (customer_id,))
    if cursor.fetchone():
        return jsonify({'error': 'Customer already has a borrowed book'}), 400

    cursor.execute("SELECT status FROM books WHERE id = %s", (book_id,))
    book = cursor.fetchone()
    if not book or book['status'] != 'available':
        return jsonify({'error': 'Book is not available'}), 400

    cursor.execute("""
        INSERT INTO borrowings (customer_id, book_id, borrow_date, late_fee)
        VALUES (%s, %s, %s, 0.00)
    """, (customer_id, book_id, borrow_date))
    cursor.execute("UPDATE books SET status = 'unavailable' WHERE id = %s", (book_id,))
    connection.commit()
    cursor.close()
    connection.close()
    return jsonify({'message': 'Borrowing created'}), 201

@app.route('/borrowings/<int:borrowing_id>/return', methods=['PUT'])
def return_book(borrowing_id):
    data = request.get_json()
    return_date_str = data.get('return_date')
    if not return_date_str:
        return jsonify({'error': 'Missing return_date'}), 400
    try:
        return_date = datetime.strptime(return_date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

    connection = create_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM borrowings WHERE id = %s", (borrowing_id,))
    borrowing = cursor.fetchone()
    if not borrowing:
        return jsonify({'error': 'Borrowing not found'}), 404

    borrow_date = borrowing['borrow_date']
    book_id = borrowing['book_id']
    days_borrowed = (return_date - borrow_date).days
    late_fee = max(0, days_borrowed - 10)

    cursor.execute(
        "UPDATE borrowings SET return_date = %s, late_fee = %s WHERE id = %s",
        (return_date, late_fee, borrowing_id)
    )
    cursor.execute("UPDATE books SET status = 'available' WHERE id = %s", (book_id,))
    connection.commit()
    cursor.close()
    connection.close()
    return jsonify({'message': 'Book returned successfully', 'late_fee': late_fee}), 200

@app.route('/borrowings', methods=['GET'])
def get_all_borrowings():
    connection = create_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("""
        SELECT b.id AS borrowing_id, c.name AS customer_name, bo.title AS book_title,
               b.borrow_date, b.return_date, b.late_fee
        FROM borrowings b
        JOIN customers c ON b.customer_id = c.id
        JOIN books bo ON b.book_id = bo.id
        ORDER BY b.borrow_date DESC
    """)
    borrowings = cursor.fetchall()
    cursor.close()
    connection.close()
    return jsonify(borrowings), 200

# --- Run the app ---
if __name__ == '__main__':
    app.run(debug=True)