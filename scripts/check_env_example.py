import sys
from pathlib import Path

REQUIRED_KEYS = {
    "APP_ENV",
    "DATABASE_URL",
    "REDIS_URL",
    "SECRET_KEY",
    "JWT_SECRET_KEY",
    "FRONTEND_API_URL",
}


def main() -> int:
    env_example = Path(".env.example")
    if not env_example.exists():
        print(".env.example missing: create it with required keys.")
        return 1

    content = env_example.read_text()
    missing = []
    for key in REQUIRED_KEYS:
        if f"{key}=" not in content:
            missing.append(key)

    if missing:
        print(".env.example is incomplete. Missing keys:")
        for k in sorted(missing):
            print(f"- {k}")
        return 1

    print(".env.example includes all required keys.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
