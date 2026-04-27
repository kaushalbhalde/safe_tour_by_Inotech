from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
import random
from datetime import datetime



app = Flask(__name__)
app.secret_key = "your_secret_key"  # Required for session handling


EMAIL = "admin@gmail.com"
PASSWORD = "1234"   

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="1234",
        database="tourist_db"
    ) 


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        lat = request.form.get('latitude')
        lon = request.form.get('longitude')
        role = request.form.get('role')

        user_id = "01"  # Hardcoded or generate your own
        group_id = "1111"  # Hardcoded group id

        if not all([name, email, password, lat, lon,role]):
            flash("Please fill all fields", "error")
            return redirect(url_for('register'))

        try:
            db = get_db_connection()
            cursor = db.cursor()

            sql = ("INSERT INTO users (user_id, name, email, password, group_id, lat, lon,role) "
                   "VALUES (%s, %s, %s, %s, %s, %s, %s,%s)")
            vals = (user_id, name, email, password, group_id, float(lat), float(lon),role)

            cursor.execute(sql, vals)
            db.commit()

            cursor.close()
            db.close()

            flash("Registration successful! Please login.", "success")
            return redirect(url_for('login'))

        except mysql.connector.Error as err:
            flash(f"Database error: {err}", "error")
            return redirect(url_for('register'))

    return render_template('register.html')

@app.route('/add_member', methods=['POST'])
def add_member():
    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')
    lat = request.form.get('latitude')
    lon = request.form.get('longitude')
    role = request.form.get('role', 'member')
    print(name, email, password, lat, lon, role)

    if not all([name, email, password, lat, lon, role]):
        flash("Please fill all fields", "error")
        return redirect(url_for('home'))

    user_id = random.randint(1000, 9999) 
    group_id = 1111  # or fetch from session or current_user

    try:
        db = get_db_connection()
        cursor = db.cursor()

        sql = ("INSERT INTO users (user_id, name, email, password, group_id, lat, lon, role) "
               "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)")
        vals = (user_id, name, email, password, group_id, float(lat), float(lon), role)
        print("About to insert:", vals)
        cursor.execute(sql, vals)
        db.commit()
        print("Insert successful, rowcount =", cursor.rowcount)
        cursor.close()
        db.close()

        flash("Member added successfully!", "success")
        return redirect(url_for('home'))

    except mysql.connector.Error as err:
        print("Database error:", err)  # debug error
        flash(f"Database error: {err}", "error")
        return redirect(url_for('home'))


# @app.route('/', methods=["GET", "POST"])
# def login():
#     if request.method == "POST":
#         email = request.form.get("email")
#         password = request.form.get("password")

#         if email == EMAIL and password == PASSWORD:
#             session["user"] = email
#             return redirect(url_for("home"))
#         else:
#             return render_template("login.html", error="Invalid username or password")

#     return render_template("login.html")

@app.route('/', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        if not email or not password:
            return render_template("login.html", error="Please enter both email and password")

        try:
            db = get_db_connection()
            cursor = db.cursor(dictionary=True)

            # Check if user exists with email and password
            sql = "SELECT * FROM users WHERE email = %s AND password = %s"
            cursor.execute(sql, (email, password))
            user = cursor.fetchone()

            cursor.close()
            db.close()

            if user:
                print(user["email"])
                print(user["role"])
                session["user"] = user["email"]  # or user["user_id"] if you prefer
                session["role"] = user["role"]   # save role too if needed
                return redirect(url_for("home"))
            else:
                return render_template("login.html", error="Invalid email or password")

        except mysql.connector.Error as err:
            return render_template("login.html", error=f"Database error: {err}")

    return render_template("login.html")


@app.route('/home')
def home():
    if "user" not in session:
        return redirect(url_for("login"))

    user_email = session["user"]
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT id,name,role,lat,lon,last_location_update,group_id  FROM users WHERE email = %s", (user_email,))
        user = cursor.fetchone()

        if not user:
            cursor.close()
            db.close()
            return render_template("index.html", username="User")

        group_id = 1111

        # Fetch all users from the same group for map locations
        cursor.execute("SELECT id ,name, lat, lon ,group_id FROM users WHERE group_id = %s", (group_id,))
        group_users = cursor.fetchall()

        cursor.execute("SELECT COUNT(*) AS count FROM users WHERE group_id = %s", (group_id,))
        total_members = cursor.fetchone()['count']

        cursor.close()
        db.close()

        for u in group_users:
            u['lat'] = float(u['lat'])
            u['lon'] = float(u['lon'])

        print(group_users)
        # Render template with user info and group user locations
        return render_template(
            "index.html",
            username=user["name"],
            role=user["role"],
            lat=user["lat"],
            id=user["id"],
            lon=user["lon"],
            group_id=user["group_id"],
            group_users=group_users,
            total_members=total_members,
            last_location_update=user["last_location_update"],
        )

    except mysql.connector.Error as err:
        # On error, fallback render with safe defaults
        return render_template(
            "index.html",
            username="User",
            group_users=[]
        )

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/location', methods=['POST'])
def location():
    lat = request.form.get('latitude')
    lon = request.form.get('longitude')
    print(f"📍 Received location: Latitude={lat}, Longitude={lon}")

    return f"Received location: Latitude={lat}, Longitude={lon}"

@app.route('/update_location', methods=['POST'])
def update_location():
    if "user" not in session:
        return redirect(url_for("login"))

    user_id = request.form.get("user_id")
    lat = request.form.get("lat")
    lon = request.form.get("lon")

    if not user_id or not lat or not lon:
        flash("Missing location data", "error")
        return redirect(url_for("home"))

    try:
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("UPDATE users SET lat = %s, lon = %s, last_location_update = NOW() WHERE id = %s", (lat, lon, user_id))
        db.commit()
        cursor.close()
        db.close()

        flash("Location updated successfully", "success")
    except Exception as e:
        flash(f"Error updating location: {str(e)}", "error")

    return redirect(url_for("home"))


@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    location = request.form.get('location')
    incident = request.form.get('incidents')  
    feedback_text = request.form.get('feedback_text')
    group_id = request.form.get('group_id')


    # Simple server-side validation
    if not location:
        flash("Location is required.")
        return redirect(url_for('feedback_page'))  # Replace with your feedback page route

    # Database insertion example (use your DB connection and code here)
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO feedback (location, incidents, feedback_text, group_id, created_at)
        VALUES (%s, %s, %s, %s, %s)
    """, (location, incident, feedback_text, group_id, datetime.now()))
    db.commit()
    cursor.close()
    db.close()

    flash("Thank you for your feedback!")
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)
