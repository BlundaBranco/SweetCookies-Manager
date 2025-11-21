/**
 * SweetCookies - Logic
 */

// Variable externa para evitar conflictos de reactividad entre Alpine y Chart.js
let chartInstance = null;

tailwind.config = {
    darkMode: 'class',
    theme: {
        extend: {
            colors: {
                primary: { 50: '#fff7ed', 500: '#f97316', 600: '#ea580c', 700: '#c2410c' }
            }
        }
    }
};

function app() {
    return {
        vista: 'dashboard',
        darkMode: false,
        pedidos: [],
        estadisticas: {
            total_pedidos: 0, total_recaudado: 0, total_cookies: 0,
            pedidos_pagados: 0, pedidos_pendientes: 0,
            produccion_total: {}, produccion_por_dia: {}
        },
        sabores: [],
        busqueda: '',
        filtroPago: '',
        toasts: [],
        modalDetalle: false,
        pedidoDetalle: null,
        pedidoEditando: null,
        formPedido: {
            dia: '', nombre: '', precio_pedido: 0, precio_envio: 0,
            direccion: '', horario: '', items: []
        },
        itemTemp: { sabor: '', cantidad: 1 },

        async init() {
            this.initTheme();
            await Promise.all([
                this.cargarSabores(),
                this.cargarPedidos(),
                this.cargarEstadisticas()
            ]);
            
            // Re-renderizar gráfico si cambiamos de tamaño de ventana
            window.addEventListener('resize', () => {
                if (this.vista === 'dashboard') this.renderChart();
            });
        },

        initTheme() {
            const savedMode = localStorage.getItem('theme');
            const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            this.darkMode = savedMode ? (savedMode === 'dark') : systemPrefersDark;
            this.applyTheme();
        },

        toggleDarkMode() {
            this.darkMode = !this.darkMode;
            localStorage.setItem('theme', this.darkMode ? 'dark' : 'light');
            this.applyTheme();
            
            // Pequeña demora para permitir que CSS actualice colores antes de redibujar
            setTimeout(() => this.renderChart(), 100);
        },

        applyTheme() {
            document.documentElement.classList.toggle('dark', this.darkMode);
        },

        async cargarSabores() {
            try {
                const res = await fetch('/api/sabores');
                const data = await res.json();
                if (data.success) this.sabores = data.sabores;
            } catch (e) { console.error(e); }
        },

        async cargarPedidos() {
            try {
                const res = await fetch('/api/pedidos');
                const data = await res.json();
                if (data.success) this.pedidos = data.pedidos;
            } catch (e) { this.showNotification('Error de conexión', 'error'); }
        },

        async cargarEstadisticas() {
            try {
                const res = await fetch('/api/estadisticas');
                const data = await res.json();
                if (data.success) {
                    this.estadisticas = data.estadisticas;
                    // Usamos nextTick para asegurar que el DOM existe
                    this.$nextTick(() => this.renderChart());
                }
            } catch (e) { console.error(e); }
        },

        renderChart() {
            const ctx = document.getElementById('chartSabores');
            // Si no estamos en la vista dashboard o no existe el canvas, salir
            if (!ctx || this.vista !== 'dashboard') return;

            // Destruir instancia anterior si existe
            if (chartInstance) {
                chartInstance.destroy();
                chartInstance = null;
            }

            const labels = Object.keys(this.estadisticas.produccion_total);
            const data = Object.values(this.estadisticas.produccion_total);

            if (labels.length === 0) return;

            const isDark = this.darkMode;
            // Colores ajustados para mejor contraste
            const colors = [
                '#fb923c', '#60a5fa', '#34d399', '#f87171', '#a78bfa', 
                '#f472b6', '#fbbf24', '#818cf8', '#2dd4bf'
            ];

            chartInstance = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: labels,
                    datasets: [{
                        data: data,
                        backgroundColor: colors,
                        borderWidth: 0,
                        hoverOffset: 10
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'right',
                            labels: {
                                color: isDark ? '#e5e7eb' : '#374151', // Texto más claro en dark mode
                                font: { size: 12, family: "'Inter', sans-serif" },
                                padding: 20,
                                boxWidth: 15
                            }
                        }
                    },
                    cutout: '75%',
                    layout: {
                        padding: 20
                    }
                }
            });
        },

        get pedidosFiltrados() {
            let result = this.pedidos;
            if (this.busqueda) {
                const term = this.busqueda.toLowerCase();
                result = result.filter(p => 
                    p.nombre.toLowerCase().includes(term) ||
                    p.dia.toLowerCase().includes(term)
                );
            }
            if (this.filtroPago) {
                const isPaid = this.filtroPago === 'pagado' ? 1 : 0;
                result = result.filter(p => p.pago === isPaid);
            }
            return result;
        },

        async togglePago(id) {
            try {
                const res = await fetch(`/api/pedidos/${id}/toggle-pago`, { method: 'POST' });
                const data = await res.json();
                if (data.success) {
                    await Promise.all([this.cargarPedidos(), this.cargarEstadisticas()]);
                    this.showNotification('Estado actualizado', 'success');
                }
            } catch (e) { this.showNotification('Error al actualizar', 'error'); }
        },

        abrirNuevoPedido() {
            this.resetForm();
            this.vista = 'nuevo';
        },

        editarPedido(pedido) {
            this.pedidoEditando = pedido;
            this.formPedido = JSON.parse(JSON.stringify(pedido));
            this.vista = 'nuevo';
        },

        cancelarEdicion() {
            this.resetForm();
            this.vista = 'pedidos';
        },

        resetForm() {
            this.pedidoEditando = null;
            this.formPedido = {
                dia: '', nombre: '', precio_pedido: 0, precio_envio: 0,
                direccion: '', horario: '', items: []
            };
            this.itemTemp = { sabor: '', cantidad: 1 };
        },

        agregarItem() {
            const { sabor, cantidad } = this.itemTemp;
            if (!sabor || cantidad < 1) return;
            this.formPedido.items.push({ sabor, cantidad: parseInt(cantidad) });
            this.itemTemp = { sabor: '', cantidad: 1 };
        },

        async guardarPedido() {
            if (!this.validateForm()) return;
            try {
                const isEdit = !!this.pedidoEditando;
                const url = isEdit ? `/api/pedidos/${this.pedidoEditando.id}` : '/api/pedidos';
                const method = isEdit ? 'PUT' : 'POST';
                const payload = {
                    ...this.formPedido,
                    precio_pedido: parseFloat(this.formPedido.precio_pedido),
                    precio_envio: parseFloat(this.formPedido.precio_envio)
                };
                const res = await fetch(url, {
                    method,
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                if (data.success) {
                    this.showNotification(isEdit ? 'Pedido actualizado' : 'Pedido creado', 'success');
                    await Promise.all([this.cargarPedidos(), this.cargarEstadisticas()]);
                    this.cancelarEdicion();
                } else {
                    this.showNotification(data.error || 'Error al guardar', 'error');
                }
            } catch (e) { this.showNotification('Error de servidor', 'error'); }
        },

        validateForm() {
            if (!this.formPedido.dia || !this.formPedido.nombre) {
                this.showNotification('Campos requeridos incompletos', 'info');
                return false;
            }
            if (this.formPedido.items.length === 0) {
                this.showNotification('Debe agregar al menos un item', 'info');
                return false;
            }
            return true;
        },

        async eliminarPedido(id) {
            if (!confirm('¿Confirmar eliminación del pedido?')) return;
            try {
                const res = await fetch(`/api/pedidos/${id}`, { method: 'DELETE' });
                if ((await res.json()).success) {
                    this.showNotification('Pedido eliminado', 'success');
                    await Promise.all([this.cargarPedidos(), this.cargarEstadisticas()]);
                }
            } catch (e) { this.showNotification('Error al eliminar', 'error'); }
        },

        verDetalle(pedido) {
            this.pedidoDetalle = pedido;
            this.modalDetalle = true;
        },

        showNotification(message, type = 'info') {
            const id = Date.now();
            this.toasts.push({ id, message, type, visible: true });
            setTimeout(() => {
                const idx = this.toasts.findIndex(t => t.id === id);
                if (idx > -1) {
                    this.toasts[idx].visible = false;
                    setTimeout(() => this.toasts.splice(idx, 1), 300);
                }
            }, 3000);
        }
    };
}