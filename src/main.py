from user_security.admin import Admin

admin = Admin(1, "admin", "admin123")

if admin.login("admin", "admin123"):
    print("Login successful")
else:
    print("Login failed")
