from flask import Flask, render_template, request, redirect, session
import json
import os
from datetime import datetime, timedelta
import pytz

app = Flask(__name__)
app.secret_key = "change_this_secret_key"

FILE = "data.json"

# 🇬🇷 Ελλάδα timezone
GREECE = pytz.timezone("Europe/Athens")

SERVICES = ["Κούρεμα", "Μούσι", "Κούρεμα + Μούσι"]
ADMIN_PASSWORD = "1234"

# --------------------
# LOAD / SAVE
# --------------------
def load():
    try:
        with open(FILE) as f:
            return json.load(f)
    except:
        return []

def save(data):
    with open(FILE, "w") as f:
        json.dump(data, f, indent=4)

# --------------------
# SLOTS
# --------------------
def generate_slots(day):
    if day == 6:
        return []

    if day == 5:
        start = 10
        end = 14
    else:
        start = 11
        end = 20

    slots = []
    current = datetime(2000, 1, 1, start, 0)
    limit = datetime(2000, 1, 1, end, 0)

    while current + timedelta(minutes=45) <= limit:
        slots.append(current.strftime("%H:%M"))
        current += timedelta(minutes=45)

    return slots

# --------------------
# FREE SLOTS
# --------------------
def get_free_slots(data, day):
    all_slots = generate_slots(day)
    booked = {d["time"].split(" ")[1] for d in data}
    return [s for s in all_slots if s not in booked]

# --------------------
# HOME
# --------------------
@app.route("/", methods=["GET", "POST"])
def index():
    data = load()

    if request.method == "POST":
        name = request.form["name"]
        phone = request.form["phone"]
        service = request.form["service"]
        date = request.form["date"]
        time = request.form["time"]

        # 🇬🇷 σωστή ώρα Ελλάδας
        now = datetime.now(GREECE)

        dt_naive = datetime.strptime(date + " " + time, "%Y-%m-%d %H:%M")
        dt = GREECE.localize(dt_naive)

        # ❗ 15 λεπτά πριν rule
        if dt - now < timedelta(minutes=15):
            return "Δεν επιτρέπεται κράτηση λιγότερο από 15 λεπτά πριν 💈"

        day = dt.weekday()

        if day == 6:
            return "Κυριακή κλειστά 💈"

        if day == 5 and (dt.hour < 10 or dt.hour >= 14):
            return "Σάββατο 10:00 - 14:00"

        if day <= 4 and (dt.hour < 11 or dt.hour >= 20):
            return "Ωράριο 11:00 - 20:00"

        # overlap check
        for d in data:
            existing = datetime.strptime(d["time"], "%Y-%m-%d %H:%M")
            existing = GREECE.localize(existing)

            if abs((existing - dt).total_seconds()) < 2700:
                return "Υπάρχει ήδη ραντεβού 💈"

        data.append({
            "name": name,
            "phone": phone,
            "service": service,
            "time": date + " " + time
        })

        save(data)
        return redirect("/success")

    return render_template(
        "index.html",
        services=SERVICES,
        slots=get_free_slots(load(), datetime.now(GREECE).weekday())
    )

# --------------------
# LOGIN
# --------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["password"] == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect("/admin")
        return "Λάθος password"

    return render_template("login.html")

# --------------------
# ADMIN
# --------------------
@app.route("/admin")
def admin():
    if not session.get("admin"):
        return redirect("/login")

    return render_template("admin.html", data=load())

# --------------------
# CANCEL
# --------------------
@app.route("/cancel/<int:index>")
def cancel(index):
    if not session.get("admin"):
        return redirect("/login")

    data = load()

    if 0 <= index < len(data):
        data.pop(index)
        save(data)

    return redirect("/admin")

# --------------------
# LOGOUT
# --------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# --------------------
# SUCCESS
# --------------------
@app.route("/success")
def success():
    return "Το ραντεβού κλείστηκε 💈"

# --------------------
# RUN
# --------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
