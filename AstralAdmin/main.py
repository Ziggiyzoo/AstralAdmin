"""
Org Discord Bot
"""
from os import environ

from src.astral_admin import AstralAdmin

# Main Method
if __name__ == "__main__":
    # Check for required environment variables
    print(environ["TOKEN"])
    print(environ["SC_API_TOKEN"])
    print(environ["FIREBASE_SECRET"])
    if "TOKEN" not in environ or environ["TOKEN"] == "":
        raise ValueError(
            "No value for Environment Variable 'TOKEN' supplied. Exiting..."
        )
    print("Running")
    token: str = environ["TOKEN"]
    Bot: AstralAdmin = AstralAdmin()
    Bot.load_extensions("src.cogs", recursive=True)
    print("cogs loaded")
    Bot.run(token)
