from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()

password = "admin123"

hash_password = bcrypt.generate_password_hash(password).decode("utf-8")

print(hash_password)