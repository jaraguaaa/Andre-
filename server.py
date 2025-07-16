from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
from werkzeug.security import generate_password_hash, check_password_hash
import secrets

app = Flask(__name__)
CORS(app)

USERS_FILE = "users.json"

def initialize_db():
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w') as f:
            json.dump({}, f)

def load_users():
    with open(USERS_FILE, 'r') as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

@app.route("/")
def index():
    return jsonify({"status": "Servidor do Thrower-X está online!"})

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return jsonify({"message": "Nome de usuário e senha são obrigatórios."}), 400
    users = load_users()
    if username in users:
        return jsonify({"message": "Este nome de usuário já está em uso."}), 409
    hashed_password = generate_password_hash(password)
    users[username] = {
        "password": hashed_password,
        "token": secrets.token_hex(16),
        "player_data": {
            "level": 1,
            "force": 10,
            "coins": 0,
            "stone_type": "small"
        }
    }
    save_users(users)
    return jsonify({"message": "Usuário registrado com sucesso."}), 201

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    users = load_users()
    if username not in users or not check_password_hash(users[username]["password"], password):
        return jsonify({"message": "Usuário ou senha inválidos."}), 401
    user = users[username]
    return jsonify({
        "message": "Login bem-sucedido",
        "token": user["token"],
        "player_data": {
            "username": username,
            **user["player_data"]
        }
    })

@app.route("/save", methods=["POST"])
def save_game():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"message": "Token de autenticação ausente."}), 401
    token = auth_header.split(" ")[1]
    users = load_users()
    username_from_token = None
    for username, user_data in users.items():
        if user_data.get("token") == token:
            username_from_token = username
            break
    if not username_from_token:
        return jsonify({"message": "Token inválido."}), 401
    progress_data = request.get_json()
    users[username_from_token]["player_data"] = {
        "level": progress_data.get("level"),
        "force": progress_data.get("force"),
        "coins": progress_data.get("coins"),
        "stone_type": progress_data.get("stone_type")
    }
    save_users(users)
    return jsonify({"message": "Progresso salvo com sucesso!"}), 200

if __name__ == "__main__":
    initialize_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)