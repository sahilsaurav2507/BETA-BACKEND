from passlib.context import CryptContext

# Create password context (same as used in the application)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Passwords to hash
passwords = {
    "prabhjotjaswal08@gmail.com": "aaAA123/",
    "sahilsaurav2507@gmail.com": "Sahilraj@123456//"
}

print("Generating bcrypt hashes for admin passwords...")
print("=" * 60)

for email, password in passwords.items():
    hashed = pwd_context.hash(password)
    print(f"\nEmail: {email}")
    print(f"Password: {password}")
    print(f"Bcrypt Hash: {hashed}")
    print("-" * 60)

print("\nMySQL Commands:")
print("=" * 60)

# Generate the MySQL commands with the actual hashes
hash1 = pwd_context.hash("aaAA123/")
hash2 = pwd_context.hash("Sahilraj@123456//")

print(f"""
-- Add first admin user
INSERT INTO users (name, email, password_hash, is_active, is_admin, created_at, updated_at) 
VALUES (
    'Prabhjot Jaswal', 
    'prabhjotjaswal08@gmail.com', 
    '{hash1}',
    TRUE, 
    TRUE, 
    NOW(), 
    NOW()
);

-- Add second admin user
INSERT INTO users (name, email, password_hash, is_active, is_admin, created_at, updated_at) 
VALUES (
    'Sahil Saurav', 
    'sahilsaurav2507@gmail.com', 
    '{hash2}',
    TRUE, 
    TRUE, 
    NOW(), 
    NOW()
);
""")
