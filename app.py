from flask import Flask, request, jsonify, send_from_directory, render_template, redirect, url_for, session
from flask_socketio import SocketIO, send
import sqlite3
import os
from flask_cors import CORS  # Importar o CORS

app = Flask(__name__)
app.secret_key = 'your_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")  # Habilitar CORS no SocketIO

# Habilitar CORS para todas as rotas
CORS(app, resources={r"/*": {"origins": "*"}})

# Banco de dados SQLite
DB_PATH = os.path.join(os.getcwd(), "users.db")  # Garante que o banco será criado no diretório atual

# Função para criar a tabela de usuários
def init_db():
    print("Verificando o banco de dados...")
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        # Criar a tabela se ela não existir
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        print("Tabela de usuários verificada/criada.")

# Função para criar o usuário padrão
def create_default_user():
    print("Verificando/criando usuário padrão...")
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password, name) VALUES (?, ?, ?)", ("x", "22", "Admin"))
            conn.commit()
            print("Usuário padrão criado com sucesso.")
        except sqlite3.IntegrityError:
            print("Usuário padrão já existe. Nenhuma ação necessária.")

# Rota para servir arquivos estáticos (HTML)
@app.route('/')
def serve_index():
    return send_from_directory(os.getcwd(), 'index.html')

@app.route('/admin')
def serve_admin():
    return send_from_directory(os.getcwd(), 'admin.html')

# Configurar o Flask para servir arquivos estáticos
@app.route('/img/<path:filename>')
def serve_images(filename):
    return send_from_directory(os.path.join(os.getcwd(), 'img'), filename)

@app.route('/<path:filename>')
def serve_static_files(filename):
    return send_from_directory(os.getcwd(), filename)

# Rota para login (ajustada para redirecionar todos para o chat)
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"redirect": None}), 400

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()

    if user and user[0] == password:
        session['username'] = username
        session['is_admin'] = (username == "x" and password == "22")  # Define se é admin
        return jsonify({"redirect": "/chat"}), 200
    else:
        return jsonify({"redirect": None}), 401

# Rota para registrar usuários (apenas você pode usar)
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    name = data.get('name')

    if not username or not password or not name:
        return jsonify({"message": "Nome, usuário e senha são obrigatórios!"}), 400

    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, password, name) VALUES (?, ?, ?)", (username, password, name))
            conn.commit()
        return jsonify({"message": "Usuário registrado com sucesso!"}), 201
    except sqlite3.IntegrityError:
        return jsonify({"message": "Usuário já existe!"}), 409

# Rota para listar todos os usuários (apenas para administradores)
@app.route('/users', methods=['GET'])
def list_users():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, name FROM users WHERE username != 'x'")
        users = cursor.fetchall()
    return jsonify(users), 200

# Rota para remover um usuário (apenas para administradores)
@app.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
    return jsonify({"message": "Usuário removido com sucesso!"}), 200

# Rota para chat (ajustada para passar a flag de admin para o template)
@app.route('/chat')
def chat():
    if 'username' in session:
        return render_template('chat.html', username=session['username'], is_admin=session.get('is_admin', False))
    return redirect(url_for('serve_index'))

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return '', 204

@socketio.on('message')
def handle_message(msg):
    print(f"Message: {msg}")
    send(msg, broadcast=True)

# Inicializar banco de dados e criar usuário padrão
if __name__ == '__main__':
    print("Inicializando o banco de dados...")
    init_db()
    print("Criando usuário padrão...")
    create_default_user()
    print("Iniciando o servidor...")

    # Usar a porta fornecida pelo Render ou a porta padrão 5000
    port = int(os.getenv("PORT", 5000))
    socketio.run(app, host='0.0.0.0', port=port)  # Usar eventlet como servidor HTTP
