from flask import Flask, render_template, redirect, url_for, flash, request
import json
import os
import webbrowser
from threading import Timer
from src.config import Config

# --- LIBRERÍAS DE BASE DE DATOS Y LOGIN ---
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, current_user, logout_user, login_required

# Inicializamos la app Flask
app = Flask(__name__)

# --- CONFIGURACIÓN ---
app.config['SECRET_KEY'] = 'bubo_alpha_secret_key_12345' # Cambia esto en producción
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'

# Extensiones
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# --- MODELO DE USUARIO ---
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    # Columna para guardar la lista de favoritos (string separado por comas)
    watchlist = db.Column(db.String(500), default="") 

# --- RUTAS ---

@app.route('/')
@login_required
def dashboard():
    json_path = Config.DATA_PROCESSED / "latest_signals.json"
    
    signals = []
    
    # 1. Intentamos leer el archivo JSON con todas las señales
    if json_path.exists():
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                all_signals = json.load(f)
            
            # 2. Lógica de Filtrado por Watchlist
            if current_user.watchlist:
                # Convertimos "AAPL, BTC" -> ['AAPL', 'BTC']
                user_tickers = [t.strip().upper() for t in current_user.watchlist.split(',') if t.strip()]
                # Filtramos solo las que el usuario quiere
                signals = [s for s in all_signals if s['ticker'] in user_tickers]
            else:
                # Si no tiene watchlist, mostramos todo (o podrías mostrar nada)
                signals = all_signals

        except Exception as e:
            print(f"Error leyendo JSON: {e}")
    
    # 3. Renderizamos pasando las SEÑALES, el USUARIO y las CATEGORÍAS (para el menú)
    return render_template(
        'dashboard.html', 
        signals=signals, 
        user=current_user,
        categories=Config.TICKER_CATEGORIES # <--- Importante para el menú
    )

@app.route('/update_watchlist', methods=['POST'])
@login_required
def update_watchlist():
    new_tickers = request.form.get('tickers')
    
    if new_tickers is not None:
        # Limpieza de datos
        cleaned_tickers = ",".join([t.strip().upper() for t in new_tickers.split(',') if t.strip()])
        
        # Guardar en BD
        current_user.watchlist = cleaned_tickers
        db.session.commit()
        flash('Watchlist actualizada con éxito.', 'success')
    
    return redirect(url_for('dashboard'))

# --- RUTAS DE AUTH (Login/Registro) ---

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user_exists = User.query.filter_by(username=username).first()
        if user_exists:
            flash('Ese usuario ya existe.', 'danger')
        else:
            hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
            user = User(username=username, password=hashed_pw)
            db.session.add(user)
            db.session.commit()
            flash('Cuenta creada. Inicia sesión.', 'success')
            return redirect(url_for('login'))
            
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Usuario o contraseña incorrectos.', 'danger')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

# --- INICIO DEL SERVIDOR ---

def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000")

if __name__ == '__main__':
    with app.app_context():
        db.create_all() # Crea la base de datos si no existe
        
    Timer(1, open_browser).start()
    app.run(debug=True, port=5000, host='0.0.0.0')