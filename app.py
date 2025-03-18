from flask import Flask, request, jsonify
import mysql.connector
from mysql.connector import Error
from datetime import datetime

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

# Run Flask app
if __name__ == '__main__':
    app.run(debug=True)