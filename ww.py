from datetime import datetime
import os
import sqlite3
from flask import Flask, redirect, render_template, request, session, url_for

app = Flask(__name__)
# Ключ для работы временной памяти сессии на экране
app.secret_key = "taxi_zen_studio_secure_key_999"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "taxi_final_v3.db")


def init_db():
    """Инициализация базы данных: создание таблиц поездок и водителей."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 1. Таблица истории поездок
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS trips (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            passenger_name TEXT,
            street_from TEXT,
            street_to TEXT,
            distance REAL,
            tariff TEXT,
            driver_name TEXT,
            cost REAL,
            timestamp TEXT
        )
    """
    )

    # 2. Таблица водителей
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS drivers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            car TEXT,
            rating REAL
        )
    """
    )

    # Заполняем водителей, если таблица пуста
    cursor.execute("SELECT COUNT(*) FROM drivers")
    if cursor.fetchone() == 0:
        drivers_data = [
            ("Алексей Смирнов", "Lada Vesta (Серый металлик)", 4.95),
            ("Дмитрий Петров", "Skoda Rapid (Белый)", 4.88),
            ("Евгений Соколов", "Kia Rio (Синий)", 4.91),
            ("Николай Морозов", "Toyota Camry (Черный)", 4.99),
            ("Сергей Волков", "Volkswagen Polo (Желтый)", 4.79),
            ("Андрей Федоров", "Hyundai Solaris (Красный)", 4.85),
        ]
        cursor.executemany(
            "INSERT INTO drivers (name, car, rating) VALUES (?, ?, ?)",
            drivers_data,
        )

    conn.commit()
    conn.close()


@app.route("/", methods=["GET", "POST"])
def index2():  # Обязательное имя функции по ТЗ
    init_db()

    if request.method == "POST":
        passenger_name = (
            request.form.get("passenger_name", "").strip() or "Пассажир"
        )
        street_from = request.form.get("street_from", "").strip() or "Пункт А"
        street_to = request.form.get("street_to", "").strip() or "Пункт Б"
        distance = float(request.form.get("distance", 1.0))
        tariff = request.form.get("tariff", "Эконом")
        driver_name = request.form.get("driver", "Алексей Смирнов")

        rates = {"Эконом": 15, "Комфорт": 25, "Бизнес": 60}
        base_fares = {"Эконом": 60, "Комфорт": 140, "Бизнес": 350}
        cost = round(
            base_fares.get(tariff, 60) + (distance * rates.get(tariff, 15)), 2
        )

        # ШАГ 1: НАДЕЖНО КЛАДЕМ ЗАКАЗ В БАЗУ ДАННЫХ SQLite
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO trips (passenger_name, street_from, street_to, distance, tariff, driver_name, cost, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                passenger_name,
                street_from,
                street_to,
                distance,
                tariff,
                driver_name,
                cost,
                datetime.now().strftime("%H:%M"),
            ),
        )
        conn.commit()
        conn.close()

        # ШАГ 2: Кладем этот же заказ во временную память экрана
        session["current_active_trip"] = {
            "passenger_name": passenger_name,
            "street_from": street_from,
            "street_to": street_to,
            "distance": distance,
            "tariff": tariff,
            "driver_name": driver_name,
            "cost": cost,
            "timestamp": datetime.now().strftime("%H:%M"),
        }

        return redirect(url_for("index2"))

    # Чтение списка водителей для выпадающего списка
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT name, car, rating FROM drivers")
    drivers_list = cursor.fetchall()
    conn.close()

    # Извлекаем текущий рейс с экрана (если он есть)
    current_trip = session.get("current_active_trip", None)

    return render_template(
        "index2.html", drivers=drivers_list, active_trip=current_trip
    )


@app.route("/complete", methods=["POST"])
def complete_order():
    """Эндпоинт для завершения поездки: стирает заказ с экрана, но оставляет в БД."""
    session.pop("current_active_trip", None)  # Стираем из временной памяти экрана
    return redirect(url_for("index2"))  # Полностью перезагружаем страницу


if __name__ == "__main__":
    app.run(debug=True, port=5002)
