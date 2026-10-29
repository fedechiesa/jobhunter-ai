"""Generate local, untracked configuration. Never overwrite an existing .env."""

import secrets
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    password = secrets.token_urlsafe(32)
    test_password = secrets.token_urlsafe(32)
    content = (root / ".env.example").read_text(encoding="utf-8")
    content = content.replace("replace_with_another_generated_password", test_password)
    content = content.replace("replace_with_generated_password", password)
    try:
        with (root / ".env").open("x", encoding="utf-8") as output:
            output.write(content)
    except FileExistsError:
        raise SystemExit(".env already exists; nothing changed.") from None
    print("Created .env with generated local credentials. Do not commit it.")


if __name__ == "__main__":
    main()
