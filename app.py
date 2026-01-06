from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
import os, json, uuid
from datetime import datetime

app = Flask(__name__)

# ======================
# SECURITY (REQUIRED)
# ======================
app.secret_key = os.environ.get("SECRET_KEY", "dev-fallback")

# ======================
# PATHS (RENDER SAFE)
# ======================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "storage.json")
USERS_FILE = os.path.join(BASE_DIR, "users.json")

UPLOAD_FOLDER = "/tmp/uploads/pdfs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ======================
# HELPERS
# ======================
def load_json(file):
    if not os.path.exists(file):
        return {"pdfs": [], "sheets": []}
    with open(file, "r") as f:
        return json.load(f)

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

def login_required():
    return "user" in session

# ======================
# AUTH
# ======================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        users = load_json(USERS_FILE)["users"]

        user = next(
            (u for u in users if u["username"] == username and u["password"] == password),
            None
        )

        if user:
            session["user"] = user["username"]
            session["team"] = user["team"]
            return redirect(url_for("dashboard"))

        return render_template("login.html", error="Invalid credentials")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ======================
# DASHBOARD
# ======================
@app.route("/")
def dashboard():
    if not login_required():
        return redirect(url_for("login"))

    return render_template(
        "dashboard.html",
        team=session["team"],
        title="Dashboard"
    )

# ======================
# PDF SECTION
# ======================
@app.route("/pdfs", methods=["GET", "POST"])
def pdfs():
    if not login_required():
        return redirect(url_for("login"))

    data = load_json(DATA_FILE)
    team = session["team"]

    if request.method == "POST":
        file = request.files["pdf"]

        uid = str(uuid.uuid4())
        filename = f"{uid}_{file.filename}"
        file.save(os.path.join(UPLOAD_FOLDER, filename))

        data.setdefault("pdfs", []).append({
            "id": uid,
            "original_name": file.filename,
            "filename": filename,
            "uploaded_at": datetime.now().strftime("%d-%m-%Y %H:%M"),
            "team": team
        })

        save_json(DATA_FILE, data)
        return redirect(url_for("pdfs"))

    team_pdfs = [p for p in data.get("pdfs", []) if p.get("team") == team]
    return render_template("pdfs.html", pdfs=team_pdfs, team=team)

@app.route("/pdfs/view/<filename>")
def view_pdf(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route("/pdfs/delete/<id>")
def delete_pdf(id):
    data = load_json(DATA_FILE)
    pdf = next(p for p in data["pdfs"] if p["id"] == id)

    try:
        os.remove(os.path.join(UPLOAD_FOLDER, pdf["filename"]))
    except:
        pass

    data["pdfs"] = [p for p in data["pdfs"] if p["id"] != id]
    save_json(DATA_FILE, data)

    return redirect(url_for("pdfs"))

# ======================
# GOOGLE SHEETS
# ======================
@app.route("/sheets", methods=["GET", "POST"])
def sheets():
    if not login_required():
        return redirect(url_for("login"))

    data = load_json(DATA_FILE)
    team = session["team"]

    if request.method == "POST":
        data.setdefault("sheets", []).append({
            "id": str(uuid.uuid4()),
            "name": request.form["name"],
            "url": request.form["url"],
            "created_at": datetime.now().strftime("%d-%m-%Y %H:%M"),
            "team": team
        })

        save_json(DATA_FILE, data)
        return redirect(url_for("sheets"))

    team_sheets = [s for s in data.get("sheets", []) if s.get("team") == team]
    return render_template("sheets.html", sheets=team_sheets, team=team)

@app.route("/sheets/edit/<id>", methods=["GET", "POST"])
def edit_sheet(id):
    data = load_json(DATA_FILE)
    sheet = next(s for s in data["sheets"] if s["id"] == id)

    if request.method == "POST":
        sheet["name"] = request.form["name"]
        sheet["url"] = request.form["url"]
        save_json(DATA_FILE, data)
        return redirect(url_for("sheets"))

    return render_template("edit_sheet.html", sheet=sheet)

@app.route("/sheets/delete/<id>")
def delete_sheet(id):
    data = load_json(DATA_FILE)
    data["sheets"] = [s for s in data["sheets"] if s["id"] != id]
    save_json(DATA_FILE, data)
    return redirect(url_for("sheets"))


# Local Run

# from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
# import os, json, uuid
# from datetime import datetime

# app = Flask(__name__)
# app.secret_key = "super-secret-key"

# UPLOAD_FOLDER = 'uploads/pdfs'
# DATA_FILE = 'storage.json'
# USERS_FILE = 'users.json'

# os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# def load_json(file):
#     with open(file, 'r') as f:
#         return json.load(f)

# def save_json(file, data):
#     with open(file, 'w') as f:
#         json.dump(data, f, indent=4)

# def login_required():
#     return 'user' in session

# UPLOAD_FOLDER = 'uploads/pdfs'
# DATA_FILE = 'storage.json'

# os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     if request.method == 'POST':
#         username = request.form['username']
#         password = request.form['password']

#         users = load_json(USERS_FILE)['users']

#         user = next(
#             (u for u in users if u['username'] == username and u['password'] == password),
#             None
#         )

#         if user:
#             session['user'] = user['username']
#             session['team'] = user['team']   
#             return redirect(url_for('dashboard'))

#         return render_template('login.html', error="Invalid credentials")

#     return render_template('login.html')

# @app.route('/logout')
# def logout():
#     session.clear()
#     return redirect(url_for('login'))

# def load_data():
#     with open(DATA_FILE, 'r') as f:
#         return json.load(f)

# def save_data(data):
#     with open(DATA_FILE, 'w') as f:
#         json.dump(data, f, indent=4)

# # ---------------- DASHBOARD ----------------
# @app.route('/')
# def dashboard():
#     if not login_required():
#         return redirect(url_for('login'))

#     return render_template(
#         'dashboard.html',
#         team=session['team'],
#         title="Dashboard"
#     )


# # ---------------- PDF SECTION ----------------
# @app.route('/pdfs', methods=['GET', 'POST'])
# def pdfs():
#     if not login_required():
#         return redirect(url_for('login'))

#     data = load_json(DATA_FILE)
#     team = session['team']

#     if request.method == 'POST':
#         file = request.files['pdf']
#         uid = str(uuid.uuid4())
#         filename = uid + "_" + file.filename
#         file.save(os.path.join(UPLOAD_FOLDER, filename))

#         data['pdfs'].append({
#             "id": uid,
#             "original_name": file.filename,
#             "filename": filename,
#             "uploaded_at": datetime.now().strftime("%d-%m-%Y %H:%M"),
#             "team": team
#         })
#         save_json(DATA_FILE, data)
#         return redirect(url_for('pdfs'))

#     team_pdfs = [p for p in data['pdfs'] if p.get('team') == team]
#     return render_template('pdfs.html', pdfs=team_pdfs, team=team)


# @app.route('/pdfs/view/<filename>')
# def view_pdf(filename):
#     return send_from_directory(UPLOAD_FOLDER, filename)

# @app.route('/pdfs/delete/<id>')
# def delete_pdf(id):
#     data = load_data()
#     pdf = next(p for p in data['pdfs'] if p['id'] == id)

#     os.remove(os.path.join(UPLOAD_FOLDER, pdf['filename']))
#     data['pdfs'] = [p for p in data['pdfs'] if p['id'] != id]
#     save_data(data)

#     return redirect(url_for('pdfs'))

# # ---------------- GOOGLE SHEETS ----------------
# @app.route('/sheets', methods=['GET', 'POST'])
# def sheets():
#     if not login_required():
#         return redirect(url_for('login'))

#     data = load_json(DATA_FILE)
#     team = session['team']

#     if request.method == 'POST':
#         data['sheets'].append({
#             "id": str(uuid.uuid4()),
#             "name": request.form['name'],
#             "url": request.form['url'],
#             "created_at": datetime.now().strftime("%d-%m-%Y %H:%M"),
#             "team": team
#         })
#         save_json(DATA_FILE, data)
#         return redirect(url_for('sheets'))

#     team_sheets = [s for s in data['sheets'] if s.get('team') == team]
#     return render_template('sheets.html', sheets=team_sheets, team=team)


# @app.route('/sheets/edit/<id>', methods=['GET', 'POST'])
# def edit_sheet(id):
#     data = load_data()
#     sheet = next(s for s in data['sheets'] if s['id'] == id)

#     if request.method == 'POST':
#         sheet['name'] = request.form['name']
#         sheet['url'] = request.form['url']
#         save_data(data)
#         return redirect(url_for('sheets'))

#     return render_template('edit_sheet.html', title="Edit Sheet", sheet=sheet)

# @app.route('/sheets/delete/<id>')
# def delete_sheet(id):
#     data = load_data()
#     data['sheets'] = [s for s in data['sheets'] if s['id'] != id]
#     save_data(data)
#     return redirect(url_for('sheets'))

# if __name__ == '__main__':
#     app.run(debug=True)