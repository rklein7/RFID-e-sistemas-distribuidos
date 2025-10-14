from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from datetime import datetime, timedelta
import sqlite3
import hashlib
import secrets
import threading
import time

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Configuração do banco de dados
DB_NAME = 'access_control.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Tabela de usuários do sistema (admins)
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Tabela de colaboradores
    c.execute('''CREATE TABLE IF NOT EXISTS collaborators (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        rfid_tag TEXT UNIQUE NOT NULL,
        has_access BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Tabela de logs de acesso
    c.execute('''CREATE TABLE IF NOT EXISTS access_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rfid_tag TEXT NOT NULL,
        collaborator_name TEXT,
        event_type TEXT NOT NULL,
        access_granted BOOLEAN,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        exit_timestamp TIMESTAMP
    )''')
    
    # Tabela de tokens de autenticação
    c.execute('''CREATE TABLE IF NOT EXISTS auth_tokens (
        token TEXT PRIMARY KEY,
        user_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    
    # Criar usuário admin padrão
    password_hash = hashlib.sha256('admin123'.encode()).hexdigest()
    try:
        c.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', 
                 ('admin', password_hash))
    except sqlite3.IntegrityError:
        pass
    
    # Inserir colaboradores de exemplo
    collaborators = [
        ('João Silva', 'RFID001', 1),
        ('Maria Santos', 'RFID002', 1),
        ('Pedro Oliveira', 'RFID003', 0),
        ('Ana Costa', 'RFID004', 1),
    ]
    
    for name, rfid, access in collaborators:
        try:
            c.execute('INSERT INTO collaborators (name, rfid_tag, has_access) VALUES (?, ?, ?)',
                     (name, rfid, access))
        except sqlite3.IntegrityError:
            pass
    
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_token(token):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''SELECT user_id FROM auth_tokens 
                 WHERE token = ? AND expires_at > datetime('now')''', (token,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def require_auth(f):
    def wrapper(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token or not token.startswith('Bearer '):
            return jsonify({'error': 'Token não fornecido'}), 401
        
        token = token.split(' ')[1]
        user_id = verify_token(token)
        if not user_id:
            return jsonify({'error': 'Token inválido ou expirado'}), 401
        
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

# Rotas de autenticação
@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Usuário e senha são obrigatórios'}), 400
    
    password_hash = hash_password(password)
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT id FROM users WHERE username = ? AND password_hash = ?',
             (username, password_hash))
    user = c.fetchone()
    
    if not user:
        conn.close()
        return jsonify({'error': 'Credenciais inválidas'}), 401
    
    # Gerar token
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now() + timedelta(hours=8)
    
    c.execute('INSERT INTO auth_tokens (token, user_id, expires_at) VALUES (?, ?, ?)',
             (token, user[0], expires_at))
    conn.commit()
    conn.close()
    
    return jsonify({'token': token, 'expires_at': expires_at.isoformat()})

# Rotas de colaboradores
@app.route('/api/collaborators', methods=['GET'])
@require_auth
def get_collaborators():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT id, name, rfid_tag, has_access, created_at FROM collaborators')
    collaborators = []
    for row in c.fetchall():
        collaborators.append({
            'id': row[0],
            'name': row[1],
            'rfid_tag': row[2],
            'has_access': bool(row[3]),
            'created_at': row[4]
        })
    conn.close()
    return jsonify(collaborators)

@app.route('/api/collaborators', methods=['POST'])
@require_auth
def create_collaborator():
    data = request.json
    name = data.get('name')
    rfid_tag = data.get('rfid_tag')
    has_access = data.get('has_access', True)
    
    if not name or not rfid_tag:
        return jsonify({'error': 'Nome e tag RFID são obrigatórios'}), 400
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute('INSERT INTO collaborators (name, rfid_tag, has_access) VALUES (?, ?, ?)',
                 (name, rfid_tag, has_access))
        conn.commit()
        collaborator_id = c.lastrowid
        conn.close()
        return jsonify({'id': collaborator_id, 'message': 'Colaborador criado com sucesso'}), 201
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'error': 'Tag RFID já cadastrada'}), 400

@app.route('/api/collaborators/<int:id>', methods=['PUT'])
@require_auth
def update_collaborator(id):
    data = request.json
    name = data.get('name')
    rfid_tag = data.get('rfid_tag')
    has_access = data.get('has_access')
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    updates = []
    params = []
    
    if name:
        updates.append('name = ?')
        params.append(name)
    if rfid_tag:
        updates.append('rfid_tag = ?')
        params.append(rfid_tag)
    if has_access is not None:
        updates.append('has_access = ?')
        params.append(has_access)
    
    if updates:
        updates.append('updated_at = CURRENT_TIMESTAMP')
        params.append(id)
        query = f'UPDATE collaborators SET {", ".join(updates)} WHERE id = ?'
        
        try:
            c.execute(query, params)
            conn.commit()
            conn.close()
            return jsonify({'message': 'Colaborador atualizado com sucesso'})
        except sqlite3.IntegrityError:
            conn.close()
            return jsonify({'error': 'Tag RFID já cadastrada'}), 400
    
    conn.close()
    return jsonify({'error': 'Nenhum dado para atualizar'}), 400

@app.route('/api/collaborators/<int:id>', methods=['DELETE'])
@require_auth
def delete_collaborator(id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('DELETE FROM collaborators WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Colaborador removido com sucesso'})

# Rota para o Raspberry Pi obter dados
@app.route('/api/rfid/collaborators', methods=['GET'])
def get_rfid_data():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT rfid_tag, name, has_access FROM collaborators')
    data = {}
    for row in c.fetchall():
        data[row[0]] = {'name': row[1], 'has_access': bool(row[2])}
    conn.close()
    return jsonify(data)

# Rota para registrar logs de acesso
@app.route('/api/logs/access', methods=['POST'])
def log_access():
    data = request.json
    rfid_tag = data.get('rfid_tag')
    collaborator_name = data.get('collaborator_name')
    event_type = data.get('event_type')  # 'entry', 'exit', 'denied', 'unknown'
    access_granted = data.get('access_granted', False)
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    if event_type == 'exit':
        # Atualizar último log de entrada
        c.execute('''UPDATE access_logs 
                     SET exit_timestamp = CURRENT_TIMESTAMP 
                     WHERE rfid_tag = ? AND exit_timestamp IS NULL 
                     ORDER BY timestamp DESC LIMIT 1''', (rfid_tag,))
    else:
        c.execute('''INSERT INTO access_logs (rfid_tag, collaborator_name, event_type, access_granted)
                     VALUES (?, ?, ?, ?)''',
                 (rfid_tag, collaborator_name, event_type, access_granted))
    
    conn.commit()
    log_id = c.lastrowid
    conn.close()
    
    # Emitir evento via WebSocket
    socketio.emit('access_event', {
        'rfid_tag': rfid_tag,
        'collaborator_name': collaborator_name,
        'event_type': event_type,
        'access_granted': access_granted,
        'timestamp': datetime.now().isoformat()
    })
    
    return jsonify({'log_id': log_id, 'message': 'Log registrado'}), 201

# Rota para obter logs
@app.route('/api/logs', methods=['GET'])
@require_auth
def get_logs():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    query = 'SELECT * FROM access_logs WHERE 1=1'
    params = []
    
    if start_date:
        query += ' AND timestamp >= ?'
        params.append(start_date)
    if end_date:
        query += ' AND timestamp <= ?'
        params.append(end_date)
    
    query += ' ORDER BY timestamp DESC LIMIT 1000'
    
    c.execute(query, params)
    logs = []
    for row in c.fetchall():
        logs.append({
            'id': row[0],
            'rfid_tag': row[1],
            'collaborator_name': row[2],
            'event_type': row[3],
            'access_granted': bool(row[4]),
            'timestamp': row[5],
            'exit_timestamp': row[6]
        })
    
    conn.close()
    return jsonify(logs)

# WebSocket para monitoramento em tempo real
@socketio.on('connect')
def handle_connect():
    print('Cliente conectado ao WebSocket')
    emit('connected', {'message': 'Conectado ao sistema de monitoramento'})

@socketio.on('disconnect')
def handle_disconnect():
    print('Cliente desconectado')

if __name__ == '__main__':
    init_db()
    print('🚀 Servidor iniciado em http://localhost:5000')
    print('📊 Dashboard: http://localhost:3000')
    print('🔐 Credenciais padrão: admin / admin123')
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)