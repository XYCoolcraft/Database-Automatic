from flask import Flask, render_template, request, redirect, url_for, session, flash
import json
import os

app = Flask(__name__)
app.secret_key = 'your_super_secret_key' # Ganti dengan kunci rahasia yang kuat!

DATABASE_FILE = 'database.json'
USERS_FILE = 'users.json'

# --- Fungsi Helper untuk Database ---
def load_database():
    if not os.path.exists(DATABASE_FILE):
        with open(DATABASE_FILE, 'w') as f:
            json.dump([], f)
    with open(DATABASE_FILE, 'r') as f:
        return json.load(f)

def save_database(data):
    with open(DATABASE_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def load_users():
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w') as f:
            json.dump({"user": "password", "admin": "admin_password"}, f, indent=4) # Default users
    with open(USERS_FILE, 'r') as f:
        return json.load(f)

# --- Routes Aplikasi Web ---

@app.route('/')
def index():
    if 'username' in session:
        if session['username'] == 'admin':
            return redirect(url_for('admin_panel'))
        else:
            return redirect(url_for('add_number_page'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users = load_users()

        if username in users and users[username] == password:
            session['username'] = username
            flash('Login berhasil!', 'success')
            if username == 'admin':
                return redirect(url_for('admin_panel'))
            else:
                return redirect(url_for('add_number_page'))
        else:
            flash('Username atau password salah!', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('Anda telah logout.', 'info')
    return redirect(url_for('login'))

@app.route('/add_number', methods=['GET', 'POST'])
def add_number_page():
    if 'username' not in session:
        flash('Anda harus login untuk mengakses halaman ini.', 'warning')
        return redirect(url_for('login'))

    if request.method == 'POST':
        nomor = request.form['nomor']
        
        # Validasi sederhana: nomor harus diawali 62 dan angka
        if not nomor.startswith('62') or not nomor[2:].isdigit():
            flash('Format nomor tidak valid. Contoh: 6281234567890', 'danger')
            return render_template('add_number.html')

        db = load_database()
        
        # Cek apakah nomor sudah ada
        for entry in db:
            if entry['nomor'] == nomor:
                flash(f'Nomor {nomor} sudah ada di database!', 'info')
                return render_template('add_number.html')

        # Tambahkan nomor baru dengan status default 'active'
        db.append({"nomor": nomor, "status": "active"})
        save_database(db)
        flash(f'Nomor {nomor} berhasil ditambahkan ke database dengan status "active"!', 'success')
        
    return render_template('add_number.html')

@app.route('/admin_panel', methods=['GET', 'POST'])
def admin_panel():
    if 'username' not in session or session['username'] != 'admin':
        flash('Akses ditolak. Anda bukan administrator.', 'danger')
        return redirect(url_for('login'))

    db = load_database()

    if request.method == 'POST':
        action = request.form.get('action')
        nomor_target = request.form.get('nomor')

        if action == 'delete' and nomor_target:
            db = [entry for entry in db if entry['nomor'] != nomor_target]
            save_database(db)
            flash(f'Nomor {nomor_target} berhasil dihapus.', 'success')
        elif action == 'toggle_status' and nomor_target:
            for entry in db:
                if entry['nomor'] == nomor_target:
                    entry['status'] = 'false' if entry['status'] == 'active' else 'active'
                    break
            save_database(db)
            flash(f'Status nomor {nomor_target} berhasil diubah.', 'success')
        elif action == 'add' and request.form.get('new_nomor'):
            new_nomor = request.form.get('new_nomor')
            # Validasi sederhana: nomor harus diawali 62 dan angka
            if not new_nomor.startswith('62') or not new_nomor[2:].isdigit():
                flash('Format nomor baru tidak valid. Contoh: 6281234567890', 'danger')
            else:
                # Cek apakah nomor sudah ada
                if any(entry['nomor'] == new_nomor for entry in db):
                    flash(f'Nomor {new_nomor} sudah ada di database!', 'info')
                else:
                    db.append({"nomor": new_nomor, "status": "active"})
                    save_database(db)
                    flash(f'Nomor {new_nomor} berhasil ditambahkan ke database dengan status "active"!', 'success')

    return render_template('admin.html', database=db)

if __name__ == '__main__':
    app.run(debug=True) # debug=True akan mereload server otomatis saat ada perubahan kode