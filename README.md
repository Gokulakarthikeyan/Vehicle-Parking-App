# 📌 Smart Vehicle Parking Management System

A full-stack web application that enables smart management of parking spaces with secure authentication, real-time spot allocation, admin monitoring, and automated cost calculation.


---

## 🚀 Features

### 👤 User
- Register & Login using JWT Authentication
- Check real-time parking lot availability
- Reserve a parking spot instantly
- Automatic cost calculation based on duration
- Release parking spot & view live status
- Download or receive parking history via email (CSV Export)

### 🛠 Admin
- Add / Edit / Disable Parking Lots (Soft delete)
- Restore previously disabled parking lots
- Auto-generate parking spots based on capacity
- Dynamic Search filtering: Users, Lots, Reservations
- Dashboard visualizations (Revenue, Usage, Occupancy)

---

## 🧱 Tech Stack

| Layer | Technology |
|------|------------|
| Frontend | Vue 3, Bootstrap 5, Axios, Vite |
| Backend | Flask, SQLAlchemy, JWT Authentication |
| Database | SQLite |
| Worker for Emails | Celery + Redis |
| Email Delivery | Flask-Mail (SMTP) |

---

## 📂 Project Structure

```bash
vehicle-parking-app/
├── backend/
│ ├── app.py
│ ├── exports/
│ ├── requirements.txt
│ └── .env
├── frontend/
│ ├── src/
│ ├── public/
│ ├── package.json
│ ├── vite.config.js
│ └── README.md
```
---

## ⚙️ Setup Instructions

### 🔹 Backend Setup

```bash
cd backend
pip install -r requirements.txt
python app.py
```
➡ Runs at: http://127.0.0.1:5000/

### 🔹 Frontend Setup

```bash
cd frontend
npm install
npm run dev
```
➡ Runs at: http://localhost:5173/

---

## 🔐 Default Login (Example)

| Role | Username | Password |
|------|----------|----------|
| Admin | admin | admin123 |
| User | Register from UI | Register from UI |	

➡ Admin Details can be changed by Replacing values in .env file

---

## 🗃 Database Schema (Tables & Columns)

### 🧑‍💼 Table: User

| Column Name   | Type        | Constraints                    |
| ------------- | ----------- | ------------------------------ |
| id            | Integer     | Primary Key                    |
| username      | String(120) | Unique, Not Null (Email/Login) |
| password_hash | String(200) | Not Null                       |
| name          | String(100) | Nullable                       |
| address       | String(200) | Nullable                       |
| pin_code      | String(10)  | Nullable                       |
| role          | String(20)  | Default = 'user'               |

### 🅿️ Table: ParkingLot

| Column Name         | Type        | Constraints             |
| ------------------- | ----------- | ----------------------- |
| id                  | Integer     | Primary Key             |
| prime_location_name | String(100) | Not Null                |
| price               | Float       | Not Null, Default = 0.0 |
| address             | String(200) | Nullable                |
| pin_code            | String(10)  | Nullable                |
| number_of_spots     | Integer     | Default = 0             |
| is_deleted          | Boolean     | Default = False         |

### 🚗 Table: ParkingSpot

| Column Name | Type       | Constraints                                 |
| ----------- | ---------- | ------------------------------------------- |
| id          | Integer    | Primary Key                                 |
| lot_id      | Integer    | Foreign Key → ParkingLot.id                 |
| status      | String(20) | Default = 'A' (A = Available, R = Reserved) |

### 🏁 Table: Reservation

| Column Name    | Type       | Constraints                                     |
| -------------- | ---------- | ----------------------------------------------- |
| id             | Integer    | Primary Key                                     |
| user_id        | Integer    | Foreign Key → User.id                           |
| lot_id         | Integer    | Foreign Key → ParkingLot.id                     |
| spot_id        | Integer    | Foreign Key → ParkingSpot.id                    |
| start_time     | DateTime   | Nullable                                        |
| end_time       | DateTime   | Nullable                                        |
| status         | String(20) | Required (‘Reserved’ / ‘Released’ / ‘Occupied’) |
| total_cost     | Float      | Nullable                                        |
| vehicle_number | String(30) | Nullable                                        |

---

## 📈 Major Highlights

| Feature                 | Description                       |
| ----------------------- | --------------------------------- |
| Cost calculation        | Based on total parking duration   |
| Soft delete             | Data never lost & can be restored |
| Secure roles            | Admin vs User access              |
| Scheduled email reports | Automated via Celery              |
| Optimized search        | Across 3 tables                   |

---

## Developer

Gokula Karthikeyan
