import sqlite3
from flask import Flask, redirect, render_template, request, url_for

app = Flask(__name__)


def init_taxi_db():
    conn = sqlite3.connect("taxi_experiment.db")
    cursor = conn.cursor()
    # Таблица для хранения истории поездок (База данных)
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS trips (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        distance REAL,
        tariff TEXT,
        cost REAL
    )
    """
    )
    conn.commit()
    conn.close()


@app.route("/", methods=["GET", "POST"])
def index():
    init_taxi_db()

    if request.method == "POST":
        # 1. Получаем данные из понятной формы на сайте
        distance = float(request.form.get("distance", 1))
        tariff = request.form.get("tariff", "Эконом")

        # 2. Проводим понятный вычислительный эксперимент (расчет цены)
        if tariff == "Эконом":
            cost = 50 + (distance * 15)  # 50 руб посадка + 15 руб за км
        elif tariff == "Комфорт":
            cost = 100 + (distance * 25)  # 100 руб посадка + 25 руб за км
        else:
            cost = 250 + (distance * 50)  # Бизнес: 250 руб посадка + 50 руб за км

        # 3. Сохраняем расчет в базу данных
        conn = sqlite3.connect("taxi_experiment.db")
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO trips (distance, tariff, cost) VALUES (?, ?, ?)",
            (distance, tariff, round(cost, 2)),
        )
        conn.commit()
        conn.close()

        return redirect(url_for("index"))

    # Загружаем из базы историю всех расчетов, чтобы показать на сайте
    conn = sqlite3.connect("taxi_experiment.db")
    cursor = conn.cursor()
    cursor.execute("SELECT distance, tariff, cost FROM trips ORDER BY id DESC")
    trips_history = cursor.fetchall()
    conn.close()

    return render_template("index.html", history=trips_history)


if __name__ == "__main__":
    app.run(debug=True, port=5002)
