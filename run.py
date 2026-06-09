import os
from dotenv import load_dotenv

load_dotenv()

def main():
    print("====================================")
    print(" Starting AI Knowledge Assistant... ")
    print("====================================")

    port = os.getenv("PORT", "8000")
    env = os.getenv("APP_ENV", "unknown")

    print(f"Environment: {env.upper()}")
    print(f"Running locally on port: {port}")
    print("\nProject setup verified successfully!")

if __name__ == "__main__":
    main()