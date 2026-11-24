from src.seeds import auth
from src.seeds.transactions import run as seed_transactions


if __name__ == "__main__":
    auth.run()
    seed_transactions()
