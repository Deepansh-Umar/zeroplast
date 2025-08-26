from app_setup import create_app, db
import models
from werkzeug.security import generate_password_hash

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("✅ Database and tables created.")

        # Seed admin user
        admin = models.User(
            username="Admin",
            password=generate_password_hash("admin123")
        )

        existing_admin = models.User.query.filter_by(username="Admin").first()
        if not existing_admin:
            db.session.add(admin)
            db.session.commit()
            print("✅ Admin user added.")
        else:
            print("ℹ️ Admin user already exists.")