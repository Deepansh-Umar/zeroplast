from datetime import datetime, timedelta
def seed_sample_data_for_impact():
    """Seed a few users and plastic logs for demo/testing. Idempotent."""
    from random import randint, choice
    usernames = ["alice", "bob", "carol"]
    items = ["bottle", "bag", "cup"]
    # Users
    for uname in usernames:
        if not models.User.query.filter_by(username=uname).first():
            u = models.User(username=uname, password=generate_password_hash("test123"), email=f"{uname}@test.com")
            db.session.add(u)
    db.session.commit()
    # Logs
    for uname in usernames:
        user = models.User.query.filter_by(username=uname).first()
        if not user:
            continue
        # Only seed if user has < 5 logs
        if models.PlasticLog.query.filter_by(user_id=user.id).count() < 5:
            for i in range(5):
                item = choice(items)
                qty = randint(1, 4)
                dt = datetime.utcnow() - timedelta(days=randint(0, 10))
                log = models.PlasticLog(item=item, quantity=qty, user_id=user.id, created_at=dt)
                db.session.add(log)
    db.session.commit()
    print("✅ Sample users and logs seeded.")
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
            password="admin@123",
            email= "admin@gmail.com"
        )

        existing_admin = models.User.query.filter_by(username="Admin").first()
        if not existing_admin:
            db.session.add(admin)
            db.session.commit()
            print("✅ Admin user added.")
        else:
            print("ℹ️ Admin user already exists.")

        # Seed sample data for impact/awareness
        seed_sample_data_for_impact()