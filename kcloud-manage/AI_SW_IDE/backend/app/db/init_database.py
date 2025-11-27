import csv
from app.models.user import User
from app.models.gpu import Flavor
from app.db.session import SessionLocal
from app.api.routes.auth import hash_password

def init_users_from_csv(csv_path):
    db = SessionLocal()
    try:
        if db.query(User).count() == 0:
            users = []
            with open(csv_path, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    user = User(
                        email=row['email'],
                        hashed_password=hash_password(row['hashed_password']),
                        role=row['role'],
                        name=row['name'],
                        department=row['department']
                    )
                    users.append(user)
            db.add_all(users)
            db.commit()
    finally:
        db.close()

def init_flavors_from_csv(csv_path):
    db = SessionLocal()
    try:
        if db.query(Flavor).count() == 0:
            flavors = []
            with open(csv_path, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                
                for row in reader:
                    flavor = Flavor(
                        gpu_name=row['gpu_name'],
                        available=int(row['available']),
                        worker_node=(row.get('worker_node') or '').strip(),  # Handle NOT NULL constraint
                        gpu_id=int((row.get('gpu_id') or 0)),
                        mig_id=int((row.get('mig_id') or 0)),
                    )
                    flavors.append(flavor)
            db.add_all(flavors)
            db.commit()
    finally:
        db.close()