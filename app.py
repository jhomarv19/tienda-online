from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import sqlite3
import json
from datetime import datetime
import uuid
import os

app = Flask(__name__)
app.secret_key = 'clave_secreta_tienda_online'
DATABASE = 'tienda.db'

# Función para obtener conexión a la base de datos
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# Inicializar sesión si no existe
@app.before_request
def before_request():
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())

# Página principal - Catálogo de productos
@app.route('/')
def index():
    conn = get_db()
    products = conn.execute('SELECT * FROM products WHERE stock > 0').fetchall()
    conn.close()
    return render_template('index.html', products=products)

# Página de administración de productos
@app.route('/admin')
def admin():
    conn = get_db()
    products = conn.execute('SELECT * FROM products').fetchall()
    conn.close()
    return render_template('admin.html', products=products)

# API REST: Obtener todos los productos
@app.route('/api/products', methods=['GET'])
def get_products():
    conn = get_db()
    products = conn.execute('SELECT * FROM products').fetchall()
    conn.close()
    return jsonify([dict(product) for product in products])

# API REST: Obtener un producto por ID
@app.route('/api/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    conn = get_db()
    product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    conn.close()
    if product:
        return jsonify(dict(product))
    return jsonify({'error': 'Producto no encontrado'}), 404

# API REST: Crear un nuevo producto
@app.route('/api/products', methods=['POST'])
def create_product():
    data = request.get_json()
    required_fields = ['name', 'price', 'stock']
    
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Campo {field} es requerido'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO products (name, description, price, stock, image_url)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        data['name'],
        data.get('description', ''),
        float(data['price']),
        int(data['stock']),
        data.get('image_url', 'https://via.placeholder.com/200x150?text=Producto')
    ))
    conn.commit()
    product_id = cursor.lastrowid
    conn.close()
    
    return jsonify({'message': 'Producto creado', 'id': product_id}), 201

# API REST: Actualizar producto
@app.route('/api/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    data = request.get_json()
    conn = get_db()
    
    # Verificar si el producto existe
    product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    if not product:
        conn.close()
        return jsonify({'error': 'Producto no encontrado'}), 404
    
    # Actualizar campos
    fields = ['name', 'description', 'price', 'stock', 'image_url']
    updates = []
    values = []
    
    for field in fields:
        if field in data:
            updates.append(f'{field} = ?')
            values.append(data[field])
    
    if not updates:
        conn.close()
        return jsonify({'error': 'No hay campos para actualizar'}), 400
    
    values.append(product_id)
    query = f'UPDATE products SET {", ".join(updates)} WHERE id = ?'
    
    conn.execute(query, values)
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Producto actualizado'})

# API REST: Eliminar producto
@app.route('/api/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    conn = get_db()
    
    # Verificar si el producto existe
    product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    if not product:
        conn.close()
        return jsonify({'error': 'Producto no encontrado'}), 404
    
    # Eliminar producto
    conn.execute('DELETE FROM products WHERE id = ?', (product_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Producto eliminado'})

# API REST: Obtener carrito
@app.route('/api/cart', methods=['GET'])
def get_cart():
    session_id = session['session_id']
    conn = get_db()
    
    cart_items = conn.execute('''
        SELECT c.id, c.product_id, c.quantity, p.name, p.price, p.image_url, 
               (p.price * c.quantity) as subtotal
        FROM cart c
        JOIN products p ON c.product_id = p.id
        WHERE c.session_id = ?
    ''', (session_id,)).fetchall()
    
    total = sum(item['subtotal'] for item in cart_items)
    
    conn.close()
    
    return jsonify({
        'items': [dict(item) for item in cart_items],
        'total': total
    })

# API REST: Agregar producto al carrito
@app.route('/api/cart', methods=['POST'])
def add_to_cart():
    data = request.get_json()
    session_id = session['session_id']
    
    if 'product_id' not in data or 'quantity' not in data:
        return jsonify({'error': 'product_id y quantity son requeridos'}), 400
    
    product_id = int(data['product_id'])
    quantity = int(data['quantity'])
    
    conn = get_db()
    
    # Verificar stock disponible
    product = conn.execute('SELECT stock FROM products WHERE id = ?', (product_id,)).fetchone()
    if not product:
        conn.close()
        return jsonify({'error': 'Producto no encontrado'}), 404
    
    if product['stock'] < quantity:
        conn.close()
        return jsonify({'error': 'Stock insuficiente'}), 400
    
    # Verificar si el producto ya está en el carrito
    existing = conn.execute('''
        SELECT * FROM cart 
        WHERE session_id = ? AND product_id = ?
    ''', (session_id, product_id)).fetchone()
    
    if existing:
        # Actualizar cantidad
        new_quantity = existing['quantity'] + quantity
        conn.execute('''
            UPDATE cart SET quantity = ? 
            WHERE session_id = ? AND product_id = ?
        ''', (new_quantity, session_id, product_id))
    else:
        # Agregar nuevo item
        conn.execute('''
            INSERT INTO cart (session_id, product_id, quantity)
            VALUES (?, ?, ?)
        ''', (session_id, product_id, quantity))
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Producto agregado al carrito'})

# API REST: Actualizar cantidad en carrito
@app.route('/api/cart/<int:item_id>', methods=['PUT'])
def update_cart_item(item_id):
    data = request.get_json()
    session_id = session['session_id']
    
    if 'quantity' not in data:
        return jsonify({'error': 'quantity es requerido'}), 400
    
    quantity = int(data['quantity'])
    
    if quantity <= 0:
        return jsonify({'error': 'La cantidad debe ser mayor a 0'}), 400
    
    conn = get_db()
    
    # Verificar si el item existe en el carrito
    item = conn.execute('''
        SELECT c.*, p.stock 
        FROM cart c
        JOIN products p ON c.product_id = p.id
        WHERE c.id = ? AND c.session_id = ?
    ''', (item_id, session_id)).fetchone()
    
    if not item:
        conn.close()
        return jsonify({'error': 'Item no encontrado en el carrito'}), 404
    
    # Verificar stock disponible
    if item['stock'] < quantity:
        conn.close()
        return jsonify({'error': 'Stock insuficiente'}), 400
    
    # Actualizar cantidad
    conn.execute('UPDATE cart SET quantity = ? WHERE id = ?', (quantity, item_id))
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Carrito actualizado'})

# API REST: Eliminar item del carrito
@app.route('/api/cart/<int:item_id>', methods=['DELETE'])
def remove_from_cart(item_id):
    session_id = session['session_id']
    conn = get_db()
    
    result = conn.execute('DELETE FROM cart WHERE id = ? AND session_id = ?', (item_id, session_id))
    conn.commit()
    conn.close()
    
    if result.rowcount == 0:
        return jsonify({'error': 'Item no encontrado en el carrito'}), 404
    
    return jsonify({'message': 'Item eliminado del carrito'})

# API REST: Finalizar compra
@app.route('/api/checkout', methods=['POST'])
def checkout():
    session_id = session['session_id']
    conn = get_db()
    
    # Obtener items del carrito
    cart_items = conn.execute('''
        SELECT c.product_id, c.quantity, p.price, p.stock, p.name
        FROM cart c
        JOIN products p ON c.product_id = p.id
        WHERE c.session_id = ?
    ''', (session_id,)).fetchall()
    
    if not cart_items:
        conn.close()
        return jsonify({'error': 'El carrito está vacío'}), 400
    
    # Verificar stock y calcular total
    total = 0
    for item in cart_items:
        if item['stock'] < item['quantity']:
            conn.close()
            return jsonify({'error': f'Stock insuficiente para {item["name"]}'}), 400
        total += item['price'] * item['quantity']
    
    # Crear orden
    cursor = conn.cursor()
    cursor.execute('INSERT INTO orders (session_id, total) VALUES (?, ?)', (session_id, total))
    order_id = cursor.lastrowid
    
    # Crear items de orden y actualizar stock
    for item in cart_items:
        # Insertar order_item
        cursor.execute('''
            INSERT INTO order_items (order_id, product_id, quantity, price)
            VALUES (?, ?, ?, ?)
        ''', (order_id, item['product_id'], item['quantity'], item['price']))
        
        # Actualizar stock
        new_stock = item['stock'] - item['quantity']
        cursor.execute('UPDATE products SET stock = ? WHERE id = ?', (new_stock, item['product_id']))
    
    # Vaciar carrito
    cursor.execute('DELETE FROM cart WHERE session_id = ?', (session_id,))
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'message': 'Compra realizada con éxito',
        'order_id': order_id,
        'total': total
    })

# Página del carrito
@app.route('/cart')
def cart_page():
    return render_template('cart.html')

if __name__ == '__main__':
    # Inicializar base de datos si no existe
    if not os.path.exists(DATABASE):
        import database
        database.init_db()
        print("Base de datos inicializada con datos de ejemplo")
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
