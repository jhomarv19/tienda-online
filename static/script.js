// Función para actualizar el contador del carrito
function updateCartCount() {
    $.ajax({
        url: '/api/cart',
        method: 'GET',
        success: function(response) {
            const itemCount = response.items.reduce((total, item) => total + item.quantity, 0);
            $('#cart-count').text(itemCount);
        },
        error: function() {
            console.error('Error al obtener el carrito');
        }
    });
}

// Agregar producto al carrito
function addToCart(productId) {
    const quantity = parseInt($('#qty-' + productId).val());
    
    if (quantity < 1) {
        alert('La cantidad debe ser al menos 1');
        return;
    }
    
    $.ajax({
        url: '/api/cart',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            product_id: productId,
            quantity: quantity
        }),
        success: function(response) {
            alert('Producto agregado al carrito');
            updateCartCount();
            
            // Actualizar la página del carrito si estamos en ella
            if (window.location.pathname === '/cart') {
                loadCart();
            }
        },
        error: function(xhr) {
            const error = xhr.responseJSON ? xhr.responseJSON.error : 'Error desconocido';
            alert('Error: ' + error);
        }
    });
}

// Cargar y mostrar el carrito
function loadCart() {
    $.ajax({
        url: '/api/cart',
        method: 'GET',
        success: function(response) {
            const container = $('#cart-items-container');
            const subtotalEl = $('#cart-subtotal');
            const totalEl = $('#cart-total');
            const checkoutBtn = $('#checkout-btn');
            const emptyMsg = $('#cart-empty-message');
            
            if (response.items.length === 0) {
                container.html('');
                subtotalEl.text('$0.00');
                totalEl.text('$0.00');
                checkoutBtn.hide();
                emptyMsg.show();
                return;
            }
            
            emptyMsg.hide();
            checkoutBtn.show();
            
            let html = '';
            let subtotal = 0;
            
            response.items.forEach(item => {
                const itemTotal = item.price * item.quantity;
                subtotal += itemTotal;
                
                html += `
                <div class="cart-item" id="cart-item-${item.id}">
                    <div class="cart-item-image">
                        <img src="${item.image_url || 'https://via.placeholder.com/100x100?text=Producto'}" alt="${item.name}">
                    </div>
                    <div class="cart-item-details">
                        <h3 class="cart-item-title">${item.name}</h3>
                        <p class="cart-item-price">$${item.price.toFixed(2)} c/u</p>
                    </div>
                    <div class="cart-item-actions">
                        <div class="cart-item-quantity">
                            <button class="quantity-btn" onclick="updateQuantity(${item.id}, ${item.quantity - 1})">-</button>
                            <span class="quantity">${item.quantity}</span>
                            <button class="quantity-btn" onclick="updateQuantity(${item.id}, ${item.quantity + 1})">+</button>
                        </div>
                        <div class="cart-item-total">
                            <strong>$${itemTotal.toFixed(2)}</strong>
                        </div>
                        <button class="remove-item" onclick="removeFromCart(${item.id})">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
                `;
            });
            
            container.html(html);
            subtotalEl.text('$' + subtotal.toFixed(2));
            totalEl.text('$' + response.total.toFixed(2));
        },
        error: function() {
            $('#cart-items-container').html('<p class="error">Error al cargar el carrito</p>');
        }
    });
}

// Actualizar cantidad en el carrito
function updateQuantity(itemId, newQuantity) {
    if (newQuantity < 1) {
        removeFromCart(itemId);
        return;
    }
    
    $.ajax({
        url: '/api/cart/' + itemId,
        method: 'PUT',
        contentType: 'application/json',
        data: JSON.stringify({
            quantity: newQuantity
        }),
        success: function() {
            loadCart();
            updateCartCount();
        },
        error: function(xhr) {
            const error = xhr.responseJSON ? xhr.responseJSON.error : 'Error desconocido';
            alert('Error: ' + error);
        }
    });
}

// Eliminar item del carrito
function removeFromCart(itemId) {
    if (!confirm('¿Eliminar este producto del carrito?')) {
        return;
    }
    
    $.ajax({
        url: '/api/cart/' + itemId,
        method: 'DELETE',
        success: function() {
            loadCart();
            updateCartCount();
        },
        error: function(xhr) {
            const error = xhr.responseJSON ? xhr.responseJSON.error : 'Error desconocido';
            alert('Error: ' + error);
        }
    });
}

// Finalizar compra
function checkout() {
    if (!confirm('¿Confirmar compra?')) {
        return;
    }
    
    $.ajax({
        url: '/api/checkout',
        method: 'POST',
        success: function(response) {
            alert(`¡Compra realizada con éxito! Número de orden: ${response.order_id}\nTotal: $${response.total.toFixed(2)}`);
            loadCart();
            updateCartCount();
            
            // Redirigir a la página principal después de 2 segundos
            setTimeout(() => {
                window.location.href = '/';
            }, 2000);
        },
        error: function(xhr) {
            const error = xhr.responseJSON ? xhr.responseJSON.error : 'Error desconocido';
            alert('Error: ' + error);
        }
    });
}

// Funciones para el panel de administración
function showAddProductModal() {
    $('#product-form')[0].reset();
    $('#product-id').val('');
    $('#modal-title').text('Nuevo Producto');
    $('#product-modal').show();
}

function closeModal() {
    $('#product-modal').hide();
}

function editProduct(productId) {
    $.ajax({
        url: '/api/products/' + productId,
        method: 'GET',
        success: function(product) {
            $('#product-id').val(product.id);
            $('#name').val(product.name);
            $('#description').val(product.description || '');
            $('#price').val(product.price);
            $('#stock').val(product.stock);
            $('#image_url').val(product.image_url || '');
            
            $('#modal-title').text('Editar Producto');
            $('#product-modal').show();
        },
        error: function() {
            alert('Error al cargar el producto');
        }
    });
}

function deleteProduct(productId) {
    if (!confirm('¿Eliminar este producto? Esta acción no se puede deshacer.')) {
        return;
    }
    
    $.ajax({
        url: '/api/products/' + productId,
        method: 'DELETE',
        success: function() {
            $('#product-' + productId).remove();
            alert('Producto eliminado');
            
            // Recargar la página para actualizar el catálogo
            if (window.location.pathname === '/') {
                window.location.reload();
            }
        },
        error: function(xhr) {
            const error = xhr.responseJSON ? xhr.responseJSON.error : 'Error desconocido';
            alert('Error: ' + error);
        }
    });
}

// Enviar formulario de producto
$('#product-form').submit(function(e) {
    e.preventDefault();
    
    const productId = $('#product-id').val();
    const method = productId ? 'PUT' : 'POST';
    const url = productId ? '/api/products/' + productId : '/api/products';
    
    const productData = {
        name: $('#name').val(),
        description: $('#description').val(),
        price: parseFloat($('#price').val()),
        stock: parseInt($('#stock').val()),
        image_url: $('#image_url').val()
    };
    
    $.ajax({
        url: url,
        method: method,
        contentType: 'application/json',
        data: JSON.stringify(productData),
        success: function(response) {
            alert(productId ? 'Producto actualizado' : 'Producto creado');
            closeModal();
            
            // Recargar la página para ver los cambios
            window.location.reload();
        },
        error: function(xhr) {
            const error = xhr.responseJSON ? xhr.responseJSON.error : 'Error desconocido';
            alert('Error: ' + error);
        }
    });
});

// Cerrar modal al hacer clic fuera
$(window).click(function(e) {
    if ($(e.target).is('#product-modal')) {
        closeModal();
    }
});

// Inicializar cuando el documento esté listo
$(document).ready(function() {
    // Actualizar contador del carrito
    updateCartCount();
    
    // Cargar carrito si estamos en esa página
    if (window.location.pathname === '/cart') {
        loadCart();
    }
});