import sqlite3
import os

DATABASE = 'tienda.db'

def get_db():
    """Conectar a la base de datos"""
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    """Inicializar la base de datos con las tablas necesarias"""
    if os.path.exists(DATABASE):
        os.remove(DATABASE)
    
    with sqlite3.connect(DATABASE) as conn:
        with open('schema.sql', 'r') as f:
            conn.executescript(f.read())
        conn.commit()
    
    # Insertar algunos productos de ejemplo
    db = get_db()
    productos_ejemplo = [
        ('Laptop Gamer', 'Laptop de alto rendimiento para gaming', 1200.00, 10, 'https://via.placeholder.com/200x150?text=Laptop'),
        ('Mouse Inalámbrico', 'Mouse ergonómico con conectividad Bluetooth', 25.50, 50, 'https://via.placeholder.com/200x150?text=Mouse'),
        ('Teclado Mecánico', 'Teclado mecánico con retroiluminación RGB', 89.99, 30, 'https://via.placeholder.com/200x150?text=Teclado'),
        ('Monitor 24"', 'Monitor Full HD 144Hz', 199.99, 15, 'https://via.placeholder.com/200x150?text=Monitor'),
        ('Auriculares', 'Auriculares con cancelación de ruido', 75.00, 25, 'https://via.placeholder.com/200x150?text=Auriculares')
    ]
    
    for producto in productos_ejemplo:
        db.execute('INSERT INTO products (name, description, price, stock, image_url) VALUES (?, ?, ?, ?, ?)', producto)
    
    db.commit()
    db.close()