from backend.app import app, db, User, ParkingLot, ParkingSpot, Reservation
from datetime import datetime, timedelta
import pytz
import random
import string

ist = pytz.timezone("Asia/Kolkata")


def insert_dummy_data():
    print("Resetting database...")

    db.drop_all()
    db.create_all()

    # ---------------- USERS (10 USERS) ----------------
    print("Creating Users...")

    user_objects = []

    address_pin_map = {
        "Porur": ["600116"],
        "Kolapakkam": ["600099"],
        "Iyyappanthangal": ["600056"],
        "Gerugambakkam": ["600117"],
        "Valasaravakkam": ["600087"],
        "Tambaram": ["600045"]
    }

    # --------------------------
    # MANUAL USER ENTRY
    # --------------------------
    manual_user = User(username="asgkarthi1508@gmail.com", name="Gokula Karthikeyan", address="Kolapakkam", pin_code="600128", role="user")
    manual_user.set_password("password123")
    db.session.add(manual_user)
    user_objects.append(manual_user)

    manual_user1 = User(username="aparnapinnamani97@gmail.com", name="Sai Annapoorna", address="Gerugambakkam", pin_code="600122", role="user")
    manual_user1.set_password("password123")
    db.session.add(manual_user1)
    user_objects.append(manual_user1)

    # List of 8 realistic Indian names
    names_list = [
        "Madhusudhan Boya",
        "Surjith Mani",
        "Rohan Gupta",
        "Ananya Reddy",
        "Vikram Singh",
        "Sneha Patel",
        "Bhuvaneswari",
        "Amitabh Joshi"
    ]

    for i, full_name in enumerate(names_list, start=1):
        # Create email from name (lowercase, remove spaces)
        first_name = full_name.split()[0]  # take first name only
        email = f"{first_name.lower()}@gmail.com"
        address = random.choice(list(address_pin_map.keys()))
        pin = random.choice(address_pin_map[address])
        u = User(username=email, name=full_name, address=address, pin_code=pin, role="user")
        u.set_password("password123")  # same password for all
        db.session.add(u)
        user_objects.append(u)

    db.session.commit()
    print("✔ 10 Realistic Users Inserted")

    # ---------------- PARKING LOTS ----------------
    lots_data = [
        ("Porur", 40.0, "Porur Junction", "600116", 10),
        ("Iyyappanthangal", 50.0, "Iyyappanthangal Bus Stand", "600077", 15),
        ("Kolapakkam", 30.0, "Kolapakkam Main Road", "600128", 10),
        ("Gerugambakkam", 35.0, "Gerugambakkam Murugan Temple", "600122", 5),
        ("Valasaravakkam", 45.0, "Arcot Road", "600087", 15),
        ("Tambaram", 55.0, "Tambaram Railway Station", "600045", 20),
    ]

    lot_objects = []

    print("Creating Lots & Spots...")

    for name, price, address, pin, num in lots_data:
        lot = ParkingLot(prime_location_name=name, price=price, address=address, pin_code=pin, number_of_spots=num)
        db.session.add(lot)
        db.session.commit()
        lot_objects.append(lot)
        for i in range(num):
            spot = ParkingSpot(lot_id=lot.id, status='A')
            db.session.add(spot)

    db.session.commit()
    print("✔ Parking Lots & Spots Inserted")

    # ---------------- RESERVATIONS (100) ----------------
    print("Creating 100 Reservations...")

    reservation_count = 100

    def generate_vehicle_number():
        # Indian State Codes (Common)
        states = ["AP","KA","KL","TN","TS"]
        # states = ["AP","AR","AS","BR","CH","DL","GA","GJ","HR","HP","JH","JK","KA", "KL","LD","MH","ML","MN","MP","MZ","NL","OD","PB","PY","RJ","SK", "TN","TS","TR","UP","UK","WB"]
        state = random.choice(states)
        rto_code = f"{random.randint(1, 50):02d}"
        series = ''.join(random.choices(string.ascii_uppercase, k=2))
        number = f"{random.randint(1, 9999):04d}"
        return f"{state}{rto_code}{series}{number}"

    for _ in range(reservation_count):
        user = random.choice(user_objects)
        lot = random.choice(lot_objects)
        spots = ParkingSpot.query.filter_by(lot_id=lot.id).all()

        # Build spot usage dict for this lot
        spot_usage = {sp.id: [] for sp in spots}
        existing_reservations = Reservation.query.filter_by(lot_id=lot.id).all()
        for r in existing_reservations:
            spot_usage[r.spot_id].append((r.start_time, r.end_time))

        # Decide active (30%) or released (70%)
        is_active = random.random() < 0.3

        selected_spot = None
        start_time = end_time = None

        # Try to find a spot with no overlap
        for sp in spots:
            # Generate start/end times
            if is_active:
                start_time = datetime.now(ist) - timedelta(days=random.randint(0, 3), hours=random.randint(1, 5))
                start_time = ist.localize(start_time.replace(tzinfo=None)) if start_time.tzinfo is None else start_time
                end_time = None
            else:
                days_back = random.randint(1, 40)
                duration_hours = random.randint(1, 12)
                start_time = datetime.now(ist) - timedelta(days=days_back, hours=random.randint(1, 10))
                end_time = start_time + timedelta(hours=duration_hours)
                start_time = ist.localize(start_time.replace(tzinfo=None)) if start_time.tzinfo is None else start_time
                end_time = ist.localize(end_time.replace(tzinfo=None)) if end_time.tzinfo is None else end_time

            # Check overlap with existing reservations
            overlap = False
            for existing_start, existing_end in spot_usage[sp.id]:
                # Make sure existing times are timezone-aware
                if existing_start.tzinfo is None:
                    existing_start = ist.localize(existing_start)
                if existing_end is not None and existing_end.tzinfo is None:
                    existing_end = ist.localize(existing_end)
                # Active reservation in existing reservations
                if existing_end is None or end_time is None:
                    overlap = True
                    break
                # Standard overlap check for past reservations
                if not (end_time <= existing_start or start_time >= existing_end):
                    overlap = True
                    break

            if not overlap:
                selected_spot = sp
                break  # found free spot

        if selected_spot is None:
            continue  # skip if no free spot

        # Update spot status
        selected_spot.status = "R" if is_active else "A"

        # Calculate cost
        if not is_active:
            total_hours = (end_time - start_time).total_seconds() / 3600
            if total_hours > 24:
                days = int(total_hours // 24)
                remaining = total_hours % 24
                daily_rate = 18 * float(lot.price)
                total_cost = round(days * daily_rate + remaining * float(lot.price))
            else:
                total_cost = round(max(total_hours, 0.25) * float(lot.price))
        else:
            total_cost = None

        # Create reservation
        reservation = Reservation(
            user_id=user.id,
            lot_id=lot.id,
            spot_id=selected_spot.id,
            start_time=start_time,
            end_time=end_time,
            status="Reserved" if is_active else "Released",
            total_cost=total_cost,
            vehicle_number=generate_vehicle_number()
        )
        db.session.add(reservation)

        # Update spot_usage
        if end_time is None:
            spot_usage[selected_spot.id].append((start_time, datetime.max.replace(tzinfo=ist)))
        else:
            spot_usage[selected_spot.id].append((start_time, end_time))

    db.session.commit()
    print("✔ 100 Dummy Reservations Added Correctly With No Overlaps")

    print("🎉 Dummy Data Inserted Successfully!")

# ------------------- MAIN -------------------
if __name__ == "__main__":
    with app.app_context():
        insert_dummy_data()
