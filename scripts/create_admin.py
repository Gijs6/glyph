import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import app
from models import User, db


def main():
    parser = argparse.ArgumentParser(description="Create or promote an admin user")
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    args = parser.parse_args()

    with app.app_context():
        user = User.query.filter_by(email=args.email).first()

        if user:
            user.role = "admin"
            db.session.commit()
            print(f"User '{args.email}' promoted to admin.")
        else:
            user = User(email=args.email, role="admin")
            try:
                user.set_password(args.password)
            except ValueError as e:
                print(f"Error: {e}")
                return
            db.session.add(user)
            db.session.commit()
            print(f"Admin user '{args.email}' created.")


if __name__ == "__main__":
    main()
