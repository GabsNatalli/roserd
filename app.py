import os
from flask import Flask, request, jsonify, session, redirect, url_for, render_template, send_from_directory
from flask_socketio import SocketIO, send
import sqlite3
from flask_cors import CORS
from werkzeug.utils import secure_filename

# Configuração do Flask
app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = os.getenv('SECRET_KEY', 'your_secret_key')  # Usar variável de ambiente para a chave secreta
socketio = SocketIO(app, cors_allowed_origins="*")  # Habilitar CORS no SocketIO

# Habilitar CORS para todas as rotas
CORS(app, resources={r"/*": {"origins": "*"}})

UPLOAD_FOLDER = os.path.join(app.static_folder, 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Caminho do banco de dados SQLite
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
                name TEXT NOT NULL,
                profile_pic TEXT,
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
            # Verificar se o usuário já existe
            cursor.execute("SELECT id FROM users WHERE username = ?", ("x",))
            user = cursor.fetchone()
            if user:
                # Atualizar o nome e a senha do usuário existente
                cursor.execute(
                    "UPDATE users SET password = ?, name = ? WHERE username = ?",
                    ("29313825", "Admin", "x")
                )
                print("Usuário padrão atualizado com sucesso.")
            else:
                # Criar o usuário padrão
                cursor.execute(
                    "INSERT INTO users (username, password, name) VALUES (?, ?, ?)",
                    ("x", "29313825", "Admin")
                )
                print("Usuário padrão criado com sucesso.")
            conn.commit()
        except sqlite3.Error as e:
            print(f"Erro ao criar/atualizar o usuário padrão: {e}")

# Rota para servir o arquivo index.html
@app.route('/')
def serve_index():
    return render_template('index.html')

# Rota para servir o arquivo chat.html
@app.route('/chat')
def serve_chat():
    if 'username' in session:
        return render_template('chat.html')
    return redirect(url_for('serve_index'))

# Rota para servir o arquivo admin.html
@app.route('/admin')
def serve_admin():
    if 'username' in session and session.get('is_admin', False):
        return render_template('admin.html')
    return redirect(url_for('serve_index'))

# Rota para servir outros arquivos estáticos
@app.route('/<path:path>')
def serve_static_files(path):
    if os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
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
        session['is_admin'] = (username == "x" and password == "29313825")  # Corrigido para verificar a senha correta
        if session['is_admin']:
            return jsonify({"redirect": "/admin"}), 200
        return jsonify({"redirect": "/chat"}), 200
    else:
        return jsonify({"redirect": None}), 401

# Rota para registrar usuários
@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    name = request.form.get('name')
    profile_pic = request.files.get('profile_pic')

    if not username or not password or not name:
        return jsonify({"message": "Nome, usuário e senha são obrigatórios!"}), 400

    profile_pic_path = None
    if profile_pic:
        filename = secure_filename(profile_pic.filename)
        profile_pic_path = os.path.join('uploads', filename)
        profile_pic.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, password, name, profile_pic) VALUES (?, ?, ?, ?)",
                (username, password, name, profile_pic_path)
            )
            conn.commit()
        return jsonify({"message": "Usuário registrado com sucesso!"}), 201
    except sqlite3.IntegrityError:
        return jsonify({"message": "Usuário já existe!"}), 409

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return '', 204

# Rota para listar todos os usuários (apenas para administradores)
@app.route('/users', methods=['GET'])
def list_users():
    if 'username' in session and session.get('is_admin', False):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, username, name, created_at FROM users WHERE username != 'x'")
            users = cursor.fetchall()
        return jsonify([{"id": user[0], "username": user[1], "name": user[2], "created_at": user[3]} for user in users]), 200
    return jsonify({"message": "Acesso negado"}), 403

# Rota para remover um usuário (apenas para administradores)
@app.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    if 'username' in session and session.get('is_admin', False):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()
        return jsonify({"message": "Usuário removido com sucesso!"}), 200
    return jsonify({"message": "Acesso negado"}), 403

@socketio.on('message')
def handle_message(data):
    username = session.get('username', 'Anônimo')
    formatted_message = f"{username}: {data}"
    send(formatted_message, broadcast=True)

# Inicializar banco de dados e criar usuário padrão
if __name__ == '__main__':
    print("Inicializando o banco de dados...")
    init_db()
    print("Criando usuário padrão...")
    create_default_user()
    print("Iniciando o servidor...")

    port = int(os.getenv("PORT", 5000))
    socketio.run(app, host='0.0.0.0', port=port)
