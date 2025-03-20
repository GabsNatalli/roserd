import os
from flask import Flask, request, jsonify, session, redirect, url_for, render_template, send_from_directory
from flask_socketio import SocketIO, send, disconnect
import sqlite3
from flask_cors import CORS
from werkzeug.utils import secure_filename
import threading
import time

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

# Função para criar o usuário padrãodo banco de dados
def update_db_structure():
    print("Atualizando a estrutura do banco de dados...")
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        # Verificar se a coluna 'profile_pic' já existe
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        if 'profile_pic' not in columns:
            print("Adicionando a coluna 'profile_pic' à tabela 'users'...")
            cursor.execute("ALTER TABLE users ADD COLUMN profile_pic TEXT")
            conn.commit()
            print("Coluna 'profile_pic' adicionada com sucesso.")
        else:
            print("A coluna 'profile_pic' já existe.")

# Atualizar a estrutura do banco de dados para adicionar a coluna de notificações
def add_notifications_column():
    print("Verificando a coluna de notificações...")
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        if 'notifications_enabled' not in columns:
            print("Adicionando a coluna 'notifications_enabled' à tabela 'users'...")
            cursor.execute("ALTER TABLE users ADD COLUMN notifications_enabled INTEGER DEFAULT 1")
            conn.commit()
            print("Coluna 'notifications_enabled' adicionada com sucesso.")
        else:
            print("A coluna 'notifications_enabled' já existe.")

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

def update_user_x():
    print("Atualizando o nome e a foto do usuário 'x'...")
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users
            SET name = ?, profile_pic = ?
            WHERE username = ?
        """, ("Ademiro", "uploads/ademiro.png", "x"))
        conn.commit()
        print("Usuário 'x' atualizado com sucesso.")

# Função para criar a tabela de mensagens
def create_messages_table():
    print("Verificando a tabela de mensagens...")
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                text TEXT NOT NULL,
                profile_pic TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        print("Tabela de mensagens verificada/criada.")

# Função para limpar mensagens a cada 24 horas
def clear_old_messages():
    while True:
        time.sleep(86400)  # 24 horas em segundos
        print("Limpando mensagens antigas...")
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM messages WHERE timestamp <= datetime('now', '-1 day')")
            conn.commit()
            print("Mensagens antigas limpas.")

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
    try:
        print("Iniciando processo de registro...")

        # Capturar os dados do formulário
        username = request.form.get('username')
        password = request.form.get('password')
        name = request.form.get('name')
        profile_pic = request.files.get('profile_pic')

        print(f"Dados recebidos: username={username}, name={name}, profile_pic={profile_pic.filename if profile_pic else 'Nenhuma'}")

        # Verificar se os campos obrigatórios estão preenchidos
        if not username or not password or not name:
            print("Erro: Nome, usuário ou senha ausentes.")
            return jsonify({"message": "Nome, usuário e senha são obrigatórios!"}), 400

        # Verificar se o nome de usuário já existe
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            existing_user = cursor.fetchone()
            if existing_user:
                print("Erro: Nome de usuário já está em uso.")
                return jsonify({"message": "Nome de usuário já está em uso!"}), 409

        # Processar a foto de perfil, se fornecida
        profile_pic_path = None
        if profile_pic:
            filename = secure_filename(profile_pic.filename)
            profile_pic_path = os.path.join('uploads', filename)
            full_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            print(f"Tentando salvar a foto de perfil em: {full_path}")
            profile_pic.save(full_path)

        # Inserir o usuário no banco de dados
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            print("Conectado ao banco de dados.")
            cursor.execute(
                "INSERT INTO users (username, password, name, profile_pic) VALUES (?, ?, ?, ?)",
                (username, password, name, profile_pic_path)
            )
            conn.commit()
            print(f"Usuário {username} registrado com sucesso.")
        return jsonify({"message": "Usuário registrado com sucesso!"}), 201

    except sqlite3.Error as db_error:
        print(f"Erro no banco de dados: {db_error}")
        return jsonify({"message": "Erro no banco de dados."}), 500
    except Exception as e:
        print(f"Erro interno no servidor: {e}")
        return jsonify({"message": "Erro interno no servidor."}), 500

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
            # Obter o nome de usuário antes de remover
            cursor.execute("SELECT username FROM users WHERE id = ?", (user_id,))
            user = cursor.fetchone()
            if user:
                username_to_disconnect = user[0]
                cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
                conn.commit()
                # Emitir evento para desconectar o usuário
                socketio.emit('force_disconnect', {"username": username_to_disconnect})
                return jsonify({"message": "Usuário removido com sucesso!"}), 200
    return jsonify({"message": "Acesso negado"}), 403

# Rota para atualizar a configuração de notificações
@app.route('/update_notifications', methods=['POST'])
def update_notifications():
    if 'username' not in session:
        return jsonify({"message": "Usuário não autenticado"}), 401

    data = request.json
    notifications_enabled = data.get('notifications_enabled')

    if notifications_enabled is None:
        return jsonify({"message": "Parâmetro inválido"}), 400

    username = session['username']
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users
            SET notifications_enabled = ?
            WHERE username = ?
        """, (1 if notifications_enabled else 0, username))
        conn.commit()

    return jsonify({"message": "Configuração de notificações atualizada com sucesso."}), 200

@socketio.on('check_session')
def check_session():
    username = session.get('username', None)
    if not username:
        disconnect()
    else:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()
            if not user:
                disconnect()  # Desconectar se o usuário não estiver mais registrado

@socketio.on('message')
def handle_message(data):
    username = session.get('username', 'Anônimo')

    # Obter a foto de perfil do usuário
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name, profile_pic FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        name = user[0] if user else username
        profile_pic = user[1] if user and user[1] else '/static/img/default-profile.png'

        # Salvar a mensagem no banco de dados
        cursor.execute("""
            INSERT INTO messages (username, text, profile_pic)
            VALUES (?, ?, ?)
        """, (name, data, profile_pic))
        conn.commit()

    formatted_message = {
        "username": name,  # Nome de exibição
        "text": data,
        "profile_pic": profile_pic  # Caminho da foto de perfil
    }
    send(formatted_message, broadcast=True)

online_users = {}  # Dicionário para armazenar usuários online e suas fotos

@socketio.on('connect')
def handle_connect():
    username = session.get('username', 'Anônimo')
    if username != 'Anônimo':
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            # Verificar se o usuário ainda está registrado
            cursor.execute("SELECT name, profile_pic, notifications_enabled FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()
            if not user:
                disconnect()  # Desconectar se o usuário não estiver mais registrado
                return
            name = user[0]
            profile_pic = user[1] if user[1] else '/static/img/default-profile.png'
            notifications_enabled = bool(user[2])
        online_users[name] = profile_pic  # Usar o nome de exibição como chave
        socketio.emit('update_users', online_users)

        # Enviar mensagens armazenadas para o cliente
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT username, text, profile_pic, timestamp FROM messages ORDER BY timestamp ASC")
            messages = cursor.fetchall()
            for msg in messages:
                socketio.emit('message', {
                    "username": msg[0],
                    "text": msg[1],
                    "profile_pic": msg[2],
                    "timestamp": msg[3]
                })

        # Enviar estado das notificações para o cliente
        socketio.emit('notifications_status', {"enabled": notifications_enabled}, room=request.sid)

@socketio.on('disconnect')
def handle_disconnect():
    username = session.get('username', 'Anônimo')
    if username != 'Anônimo':
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()
            name = user[0] if user else username  # Usar o nome de exibição
        if name in online_users:
            del online_users[name]
        socketio.emit('update_users', online_users)

if __name__ == '__main__':
    print("Inicializando o banco de dados...")
    init_db()
    update_db_structure()  # Atualizar a estrutura do banco de dados
    add_notifications_column()  # Adicionar a coluna de notificações
    create_messages_table()  # Criar a tabela de mensagens
    print("Criando usuário padrão...")
    create_default_user()
    update_user_x()  # Atualizar o nome e a foto do usuário 'x'

    # Iniciar a tarefa de limpeza de mensagens
    threading.Thread(target=clear_old_messages, daemon=True).start()

    print("Iniciando o servidor...")
    port = int(os.getenv("PORT", 5000))
    socketio.run(app, host='0.0.0.0', port=port)