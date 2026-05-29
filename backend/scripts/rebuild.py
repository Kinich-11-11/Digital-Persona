from backend.config import get_settings
from backend.pipeline import rebuild_all


if __name__ == "__main__":
    stats = rebuild_all(get_settings())
    print(stats)
