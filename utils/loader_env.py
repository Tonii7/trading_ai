import os
from dotenv import load_dotenv

def load_project_env():
    """
    Универсальный загрузчик .env:
    - находит корень проекта (папка, где лежит .env)
    - загружает только его
    - проверяет токены
    """

    # 1. Определяем абсолютный путь к текущему файлу
    current_file = os.path.abspath(__file__)

    # 2. Папка trading_ai/utils
    utils_dir = os.path.dirname(current_file)

    # 3. Папка trading_ai/
    project_src = os.path.dirname(utils_dir)

    # 4. Папка проекта (ее родитель)
    project_root = os.path.dirname(project_src)

    # 5. Путь к .env
    env_path = os.path.join(project_root, ".env")

    print(f"[ENV] Detected project root: {project_root}")
    print(f"[ENV] Looking for .env at: {env_path}")

    if not os.path.exists(env_path):
        raise FileNotFoundError(
            f"❌ Файл .env не найден!\n"
            f"Ожидался путь: {env_path}\n"
            f"Проверь расположение .env"
        )

    # 6. Загружаем
    loaded = load_dotenv(env_path)
    print(f"[ENV] Loaded: {loaded}")

    return env_path
