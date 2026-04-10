from database import SessionLocal, init_db, Customer

init_db()
db = SessionLocal()

# Clear existing data
db.query(Customer).delete()

customers = [
    Customer(name="Aarav Sharma", gender="Male", location="Mumbai"),
    Customer(name="Priya Patel", gender="Female", location="Mumbai"),
    Customer(name="Rohan Gupta", gender="Male", location="Delhi"),
    Customer(name="Ananya Singh", gender="Female", location="Bangalore"),
    Customer(name="Vikram Iyer", gender="Male", location="Chennai"),
    Customer(name="Sneha Reddy", gender="Female", location="Hyderabad"),
    Customer(name="Kavya Nair", gender="Female", location="Mumbai"),
]

db.add_all(customers)
db.commit()
print(f"✅ Seeded {len(customers)} customers successfully!")
db.close()

