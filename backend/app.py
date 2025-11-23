# Simple Signdrop Backend
from flask import Flask, request, jsonify
from flask_cors import CORS
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os
import base64
import json

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Simple in-memory storage
users = {}
files_db = {}

# ===== CRYPTO FUNCTIONS =====
def encrypt_aes(data, key):
    iv = os.urandom(12)
    cipher = Cipher(algorithms.AES(key), modes.GCM(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(data) + encryptor.finalize()
    return base64.b64encode(iv + ciphertext + encryptor.tag).decode()

def decrypt_aes(encrypted_data, key):
    data = base64.b64decode(encrypted_data)
    iv = data[:12]
    ciphertext = data[12:-16]
    tag = data[-16:]
    cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=default_backend())
    decryptor = cipher.decryptor()
    return decryptor.update(ciphertext) + decryptor.finalize()

def sign_data(data, private_key):
    signature = private_key.sign(data, padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH), hashes.SHA256())
    return base64.b64encode(signature).decode()

def verify_data(data, signature, public_key):
    try:
        public_key.verify(base64.b64decode(signature), data, padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH), hashes.SHA256())
        return True
    except:
        return False

# ===== API ENDPOINTS =====
@app.route('/api/register', methods=['POST'])
def register():
    name = request.json['name']
    
    # Generate keys
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048, backend=default_backend())
    public_key = private_key.public_key()
    
    users[name] = {
        'private_key': private_key,
        'public_key': public_key,
        'files_sent': [],
        'files_received': []
    }
    
    return jsonify({'status': 'success', 'user_id': name})

@app.route('/api/get-user/<name>', methods=['GET'])
def get_user(name):
    if name not in users:
        return jsonify({'status': 'error', 'message': 'User not found'}), 404
    
    public_key_pem = users[name]['public_key'].public_bytes(
        encoding=__import__('cryptography').hazmat.primitives.serialization.Encoding.PEM,
        format=__import__('cryptography').hazmat.primitives.serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    return jsonify({'status': 'success', 'public_key': base64.b64encode(public_key_pem).decode()})

@app.route('/api/send-file', methods=['POST'])
def send_file():
    sender = request.json['sender']
    receiver = request.json['receiver']
    content = request.json['content'].encode()
    filename = request.json.get('filename', 'file.txt')
    
    if sender not in users or receiver not in users:
        return jsonify({'status': 'error', 'message': 'Invalid user'}), 400
    
    # Generate encryption key
    enc_key = os.urandom(32)
    
    # Sign and encrypt
    signature = sign_data(content, users[sender]['private_key'])
    encrypted_content = encrypt_aes(content, enc_key)
    
    # Create file package
    file_id = base64.b64encode(os.urandom(16)).decode()
    package = {
        'file_id': file_id,
        'sender': sender,
        'content': encrypted_content,
        'signature': signature,
        'filename': filename,
        'key': base64.b64encode(enc_key).decode(),
        'receiver': receiver
    }
    
    files_db[file_id] = package
    users[sender]['files_sent'].append(file_id)
    
    return jsonify({'status': 'success', 'file_id': file_id, 'filename': filename})

@app.route('/api/receive-file', methods=['POST'])
def receive_file():
    receiver = request.json['receiver']
    file_id = request.json['file_id']
    
    if file_id not in files_db:
        return jsonify({'status': 'error', 'message': 'File not found'}), 404
    
    package = files_db[file_id]
    
    if package['receiver'] != receiver:
        return jsonify({'status': 'error', 'message': 'Not authorized'}), 403
    
    # Decrypt
    key = base64.b64decode(package['key'])
    decrypted = decrypt_aes(package['content'], key)
    
    # Verify signature
    sender_public_key = users[package['sender']]['public_key']
    is_valid = verify_data(decrypted, package['signature'], sender_public_key)
    
    users[receiver]['files_received'].append(file_id)
    
    return jsonify({
        'status': 'success',
        'content': decrypted.decode(),
        'filename': package['filename'],
        'sender': package['sender'],
        'signature_valid': is_valid
    })

@app.route('/api/revoke/<file_id>', methods=['POST'])
def revoke_file(file_id):
    if file_id not in files_db:
        return jsonify({'status': 'error', 'message': 'File not found'}), 404
    
    del files_db[file_id]
    return jsonify({'status': 'success', 'message': 'File revoked'})

@app.route('/api/corrupt-file', methods=['POST'])
def corrupt_file():
    """Simulate tampering - corrupts a file package for testing"""
    file_id = request.json.get('file_id')
    
    if file_id not in files_db:
        return jsonify({'status': 'error', 'message': 'File not found'}), 404
    
    # Create corrupted copy
    package = files_db[file_id].copy()
    encrypted_data = base64.b64decode(package['content'])
    
    # Corrupt the last 10 bytes
    corrupted = encrypted_data[:-10] + b'CORRUPTED!!'
    package['content'] = base64.b64encode(corrupted).decode()
    
    # Return corrupted package
    return jsonify({
        'status': 'success',
        'package': package,
        'message': 'File corrupted for testing'
    })

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'users': len(users)})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
