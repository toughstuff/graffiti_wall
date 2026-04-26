import sqlite3
import json
from flask import Flask, render_template
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config["SECRET_KEY"] = "graffiti-wall-secret"
socketio = SocketIO(app, cors_allowed_origins="*")

DB_PATH = "walls.db"

WALLS = ["Wall 1", "Wall 2", "Wall 3", "Wall 4", "Wall 5"]

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS strokes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            wall TEXT NOT NULL,
            data TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def get_strokes(wall):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT data FROM strokes WHERE wall = ?", (wall,))
    rows = c.fetchall()
    conn.close()
    return [json.loads(r[0]) for r in rows]

def save_stroke(wall, stroke):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO strokes (wall, data) VALUES (?, ?)", (wall, json.dumps(stroke)))
    conn.commit()
    conn.close()

def clear_wall(wall):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM strokes WHERE wall = ?", (wall,))
    conn.commit()
    conn.close()

@app.route("/")
def index():
    return render_template("index.html", walls=WALLS)

@socketio.on("join_wall")
def handle_join(data):
    wall = data.get("wall")
    strokes = get_strokes(wall)
    emit("load_strokes", {"strokes": strokes})

@socketio.on("draw")
def handle_draw(data):
    wall = data.get("wall")
    stroke = data.get("stroke")
    save_stroke(wall, stroke)
    emit("draw", {"stroke": stroke}, broadcast=True, include_self=False)

@socketio.on("clear")
def handle_clear(data):
    wall = data.get("wall")
    clear_wall(wall)
    emit("clear", broadcast=True)

if __name__ == "__main__":
    init_db()
    socketio.run(app, host="0.0.0.0", port=5000, debug=False)