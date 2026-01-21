# ------------------------------
# testing_mail.py (ADMIN-SKIP ENABLED)
# ------------------------------

from app import (
    send_daily_reminder,
    send_monthly_report,
    task_generate_csv_and_email,
    app
)
from app import db, User

MAIL_RECIVER = app.config['MAIL_DEFAULT_SENDER']   # NEW: correct sender/fallback


def test_daily_reminder_all():
    with app.app_context():
        print("Triggering daily reminder for ALL users...")

        users = User.query.all()
        for user in users:
            if user.role == "admin":
                print(f"Skipping admin user (daily reminder): {user.username}")
                continue

            print(f"Sending daily reminder → {user.username}")
            result = send_daily_reminder(user_id=user.id)
            print("Result:", result)


def test_daily_reminder_for_user(email):
    with app.app_context():
        print(f"Testing daily reminder for: {email}")
        user = User.query.filter_by(username=email).first()

        if not user:
            print(f"User not found → using MAIL_DEFAULT_SENDER ({MAIL_RECIVER})")
            result = send_daily_reminder(user_id=999999)
            print("Fallback daily reminder result:", result)
            return

        if user.role == "admin":
            print("This user is an admin → skipping daily reminder.")
            return

        result = send_daily_reminder(user_id=user.id)
        print("Daily reminder result:", result)


def test_monthly_report_all():
    with app.app_context():
        print("Triggering monthly report for ALL users...")

        users = User.query.all()
        for user in users:
            if user.role == "admin":
                print(f"Skipping admin user (monthly report): {user.username}")
                continue

            print(f"Sending monthly report → {user.username}")
            result = send_monthly_report(user_id=user.id)
            print("Result:", result)


def test_monthly_report_for_user(email):
    with app.app_context():
        print(f"Testing monthly report for: {email}")
        user = User.query.filter_by(username=email).first()

        if not user:
            print(f"User not found → using MAIL_DEFAULT_SENDER ({MAIL_RECIVER})")
            result = send_monthly_report(user_id=999999)
            print("Fallback monthly report result:", result)
            return

        if user.role == "admin":
            print("This user is an admin → skipping monthly report.")
            return

        result = send_monthly_report(user_id=user.id)
        print("Monthly report result:", result)


def test_export_csv_all():
    with app.app_context():
        users = User.query.all()
        print(f"Triggering CSV export for ALL ({len(users)}) users...")

        for user in users:
            if user.role == "admin":
                print(f"Skipping admin user (CSV export): {user.username}")
                continue

            print(f"Exporting CSV for {user.username} (User ID: {user.id})")
            result = task_generate_csv_and_email(user.id)
            print("CSV export result:", result)


def test_export_csv_for_user(email):
    with app.app_context():
        print(f"Testing CSV export for: {email}")
        user = User.query.filter_by(username=email).first()

        if not user:
            print(f"User not found → cannot export CSV")
            return

        if user.role == "admin":
            print("This user is an admin → skipping CSV export.")
            return

        result = task_generate_csv_and_email(user.id)
        print("CSV export result:", result)


# ---------------------------------------
# MAIN ENTRY POINT
# ---------------------------------------
if __name__ == "__main__":

    email = "asgkarthi1508@gmail.com"   # change if needed

    print("\n------ CELERY TASK TESTER ------")

    print("\n2️⃣ Daily Reminder (Specific user)")
    test_daily_reminder_for_user(email)

    print("\n4️⃣ Monthly Report (Specific user)")
    test_monthly_report_for_user(email)

    print("\n6️⃣ CSV Export (Specific user)")
    test_export_csv_for_user(email)

    #print("\n1️⃣ Daily Reminder (ALL users)") 
    #test_daily_reminder_all() 
    #print("\n3️⃣ Monthly Report (ALL users)") 
    #test_monthly_report_all() 
    #print("\n5️⃣ CSV Export (ALL users)") 
    #test_export_csv_all()
    print("\n------ DONE ------\n")
