from flask import Flask, request, jsonify
import mysql.connector
from mysql.connector import Error
from datetime import datetime
import os

app = Flask(__name__)

# Database Connection Setup
def create_connection():
    try:
        connection = mysql.connector.connect(
            host="cis2368.cvmow1hsmi4f.us-east-1.rds.amazonaws.com",
            user="admin",
            password="Cis2368!",
            database="FinalProject"
        )
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

# Ensure tables exist
def create_tables():
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS books (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(200) NOT NULL,
                author VARCHAR(200) NOT NULL,
                genre VARCHAR(100) NOT NULL,
                status VARCHAR(20) DEFAULT 'available'
            )
        """)
        connection.commit()
        cursor.close()
        connection.close()

# Call function to create tables
create_tables()

# CRUD Operations for Books
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
    try:
        data = request.get_json()
        if not data or not all(key in data for key in ['title', 'author', 'genre']):
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

    except Error as e:
        return jsonify({'error': str(e)}), 500

@app.route('/books/<int:book_id>', methods=['PUT'])
def update_book(book_id):
    try:
        data = request.get_json()
        connection = create_connection()
        if not connection:
            return jsonify({'error': 'Database connection failed'}), 500

        cursor = connection.cursor()
        sql = "UPDATE books SET title=%s, author=%s, genre=%s, status=%s WHERE id=%s"
        values = (data.get('title'), data.get('author'), data.get('genre'), data.get('status', 'available'), book_id)
        cursor.execute(sql, values)
        connection.commit()

        if cursor.rowcount == 0:
            return jsonify({'error': 'Book not found'}), 404

        cursor.close()
        connection.close()

        return jsonify({'message': 'Book updated successfully!'}), 200

    except Error as e:
        return jsonify({'error': str(e)}), 500

@app.route('/books/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    try:
        connection = create_connection()
        if not connection:
            return jsonify({'error': 'Database connection failed'}), 500

        cursor = connection.cursor()
        sql = "DELETE FROM books WHERE id=%s"
        cursor.execute(sql, (book_id,))
        connection.commit()

        if cursor.rowcount == 0:
            return jsonify({'error': 'Book not found'}), 404

        cursor.close()
        connection.close()

        return jsonify({'message': 'Book deleted successfully!'}), 200

    except Error as e:
        return jsonify({'error': str(e)}), 500

@app.route('/customers', methods=['GET'])
def get_customers():
    connection = create_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT id, name, email FROM customers")  # Don't send passwords
    customers = cursor.fetchall()
    cursor.close()
    connection.close()
    return jsonify(customers), 200

@app.route('/customers', methods=['POST'])
def add_customer():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')

    if not name or not email or not password:
        return jsonify({'error': 'Missing fields'}), 400

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    connection = create_connection()
    cursor = connection.cursor()
    sql = "INSERT INTO customers (name, email, password) VALUES (%s, %s, %s)"
    cursor.execute(sql, (name, email, hashed_password))
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
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        sql = "UPDATE customers SET name=%s, email=%s, password=%s WHERE id=%s"
        values = (name, email, hashed_password, customer_id)
    else:
        sql = "UPDATE customers SET name=%s, email=%s WHERE id=%s"
        values = (name, email, customer_id)

    cursor.execute(sql, values)
    connection.commit()
    cursor.close()
    connection.close()
    return jsonify({'message': 'Customer updated'}), 200

@app.route('/customers/<int:customer_id>', methods=['DELETE'])
def delete_customer(customer_id):
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM customers WHERE id=%s", (customer_id,))
    connection.commit()
    cursor.close()
    connection.close()
    return jsonify({'message': 'Customer deleted'}), 200

from datetime import datetime

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

    # Check if customer already borrowed a book
    cursor.execute("""
        SELECT * FROM borrowings
        WHERE customer_id = %s AND return_date IS NULL
    """, (customer_id,))
    if cursor.fetchone():
        return jsonify({'error': 'Customer already has a borrowed book'}), 400

    # Check if book is available
    cursor.execute("SELECT status FROM books WHERE id = %s", (book_id,))
    book = cursor.fetchone()
    if not book or book['status'] != 'available':
        return jsonify({'error': 'Book is not available'}), 400

    # Insert borrowing
    cursor.execute("""
        INSERT INTO borrowings (customer_id, book_id, borrow_date, late_fee)
        VALUES (%s, %s, %s, 0.00)
    """, (customer_id, book_id, borrow_date))

    # Update book status to 'unavailable'
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

    # Get borrow info
    cursor.execute("SELECT * FROM borrowings WHERE id = %s", (borrowing_id,))
    borrowing = cursor.fetchone()
    if not borrowing:
        return jsonify({'error': 'Borrowing not found'}), 404

    borrow_date = borrowing['borrow_date']
    book_id = borrowing['book_id']

    # Calculate late fee
    days_borrowed = (return_date - borrow_date).days
    late_fee = max(0, days_borrowed - 10)

    # Update borrowing record
    cursor.execute("""
        UPDATE borrowings
        SET return_date = %s, late_fee = %s
        WHERE id = %s
    """, (return_date, late_fee, borrowing_id))

    # Mark book as available again
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

# Run Flask app
if __name__ == '__main__':
    app.run(debug=True)