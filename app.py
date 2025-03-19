from flask import Flask, request, jsonify, send_from_directory, session, redirect, url_for
from flask_socketio import SocketIO, send
import sqlite3
import os
from flask_cors import CORS

app = Flask(__name__, static_folder='.', static_url_path='/')  # Servir arquivos estáticos da raiz do projeto
app.secret_key = 'your_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")  # Habilitar CORS no SocketIO

# Habilitar CORS para todas as rotas
CORS(app, resources={r"/*": {"origins": "*"}})

# Banco de dados SQLite
DB_PATH = os.path.join(os.getcwd(), "users.db")

# Função para criar a tabela de usuários
def init_db():
    print("Verificando o banco de dados...")
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
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

# Rota para servir o arquivo index.html
@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

# Rota para servir o arquivo chat.html
@app.route('/chat')
def serve_chat():
    return send_from_directory(app.static_folder, 'chat.html')

# Rota para servir o arquivo admin.html
@app.route('/admin')
def serve_admin():
    return send_from_directory(app.static_folder, 'admin.html')

# Rota para servir outros arquivos estáticos
@app.route('/<path:path>')
def serve_static_files(path):
    try:
        return send_from_directory(app.static_folder, path)
    except:
        return "Arquivo não encontrado.", 404

# Rota para login
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
        session['is_admin'] = (username == "x" and password == "22")
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

# Rota para chat (ajustada para passar o nome do usuário para o chat)
@app.route('/chat')
def chat():
    if 'username' in session:
        username = session['username']
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()
            name = user[0] if user else username  # Usar o nome registrado ou o username como fallback
        return send_from_directory(app.static_folder, 'chat.html')
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

    port = int(os.getenv("PORT", 5000))
    socketio.run(app, host='0.0.0.0', port=port)
