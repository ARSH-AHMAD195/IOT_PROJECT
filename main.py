from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import sqlite3
from datetime import datetime
from zoneinfo import ZoneInfo

app = FastAPI()

templates = Jinja2Templates(directory="templates")

app.mount("/static", StaticFiles(directory="static"), name="static")

# =========================
# DATABASE
# =========================

conn = sqlite3.connect("sensors.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT,
    password TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS records(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    temperature TEXT,
    humidity TEXT,
    time TEXT,
    date TEXT
)
""")

conn.commit()

# =========================
# HOME LOGIN PAGE
# =========================

@app.get("/", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# =========================
# REGISTER PAGE
# =========================

@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

# =========================
# REGISTER USER
# =========================

@app.post("/register")
def register(
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...)
):

    cursor.execute(
        "INSERT INTO users(name,email,password) VALUES(?,?,?)",
        (name, email, password)
    )

    conn.commit()

    return RedirectResponse("/", status_code=302)

# =========================
# LOGIN
# =========================

@app.post("/login")
def login(
    email: str = Form(...),
    password: str = Form(...)
):

    cursor.execute(
        "SELECT * FROM users WHERE email=? AND password=?",
        (email, password)
    )

    user = cursor.fetchone()

    if user:

        response = RedirectResponse("/dashboard", status_code=302)

        response.set_cookie(key="username", value=user[1])

        return response

    return RedirectResponse("/", status_code=302)

# =========================
# DASHBOARD
# =========================

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):

    username = request.cookies.get("username")

    cursor.execute(
        "SELECT * FROM records ORDER BY id DESC LIMIT 1"
    )

    latest = cursor.fetchone()

    latest_temp = "No Data"
    latest_humidity = "No Data"
    latest_time = "-"
    latest_date = "-"

    if latest:
        latest_temp = latest[1]
        latest_humidity = latest[2]
        latest_time = latest[3]
        latest_date = latest[4]

    cursor.execute(
        "SELECT * FROM records ORDER BY id DESC"
    )

    records = cursor.fetchall()

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "username": username,
            "latest_temp": latest_temp,
            "latest_humidity": latest_humidity,
            "latest_time": latest_time,
            "latest_date": latest_date,
            "records": records
        }
    )

# =========================
# SAVE LCD TEXT
# =========================

@app.post("/save-lcd")
def save_lcd(
    text: str = Form(...)
):

    with open("lcd.txt", "w") as file:
        file.write(text)

    return RedirectResponse("/dashboard", status_code=302)

# =========================
# FETCH LCD TEXT API
# =========================

@app.get("/get-lcd")
def get_lcd():

    try:
        with open("lcd.txt", "r") as file:
            data = file.read()

        return PlainTextResponse(data)

    except:
        return PlainTextResponse("HELLO")

# =========================
# SAVE SENSOR DATA API
# =========================

@app.get("/save-data")
def save_data(
    temperature: str,
    humidity: str
):

    now = datetime.now(ZoneInfo("Asia/Kolkata"))

    current_time = now.strftime("%I:%M %p")
    current_date = now.strftime("%d-%m-%Y")

    cursor.execute(
        """
        INSERT INTO records(
            temperature,
            humidity,
            time,
            date
        )
        VALUES(?,?,?,?)
        """,
        (
            temperature,
            humidity,
            current_time,
            current_date
        )
    )

    conn.commit()

    return {
        "message": "Data Saved"
    }

# =========================
# DELETE RECORD
# =========================

@app.get("/delete/{id}")
def delete_record(id: int):

    cursor.execute(
        "DELETE FROM records WHERE id=?",
        (id,)
    )

    conn.commit()

    return RedirectResponse("/dashboard", status_code=302)

# =========================
# LOGOUT
# =========================

@app.get("/logout")
def logout():

    response = RedirectResponse("/", status_code=302)

    response.delete_cookie("username")

    return response