import json
import subprocess
import os
import zlib
from hashlib import sha1
from typing import List, Dict, Tuple

def load_config(config_path: str) -> Dict[str, str]:
    """Загрузить конфигурацию из JSON файла."""
    with open(config_path, 'r') as f:
        return json.load(f)

def get_commits(repo_path: str, tag_name: str, previous_tag: str = None) -> List[Tuple[str, str, str]]:
    """Получить список коммитов для указанного тега."""
    if previous_tag:
        command = f'git -C "{repo_path}" log "{previous_tag}..{tag_name}" --pretty=format:"%H|%ad|%an" --date=iso'
    else:
        command = f'git -C "{repo_path}" log "{tag_name}" --pretty=format:"%H|%ad|%an" --date=iso'
    
    print(f"Executing command: {command}")  # Отладочная информация
    result = subprocess.run(command, shell=True, text=True, capture_output=True)

    if result.returncode != 0:
        raise Exception(f"Error getting commits: {result.stderr.strip()}")

    commits = []
    for line in result.stdout.splitlines():
        if line.strip():
            commit_hash, commit_date, commit_author = line.split('|')
            commit_message = get_commit_message(repo_path, commit_hash)
            commits.append((commit_hash, commit_date, commit_author, commit_message))

    print(f"Found {len(commits)} commits for tag '{tag_name}'.")  # Вывод количества коммитов
    return commits

def get_commit_message(repo_path: str, commit_hash: str) -> str:
    """Получить сообщение коммита по его хешу."""
    command = f'git -C "{repo_path}" log -1 --pretty=%B {commit_hash}'
    result = subprocess.run(command, shell=True, text=True, capture_output=True)
    if result.returncode != 0:
        raise Exception(f"Error getting commit message: {result.stderr.strip()}")
    return result.stdout.strip()

def read_git_object(repo_path: str, object_hash: str) -> str:
    """Читать объект Git и возвращать его содержимое как строку."""
    object_path = os.path.join(repo_path, '.git', 'objects', object_hash[:2], object_hash[2:])
    try:
        with open(object_path, 'rb') as f:
            compressed_contents = f.read()
            decompressed_contents = zlib.decompress(compressed_contents)
            return decompressed_contents.decode('utf-8')
    except FileNotFoundError:
        raise Exception(f"Object {object_hash} not found.")
    except Exception as e:
        raise Exception(f"Error reading object {object_hash}: {str(e)}")

def get_object_hash(file_contents: str) -> str:
    """Вычислить SHA-1 хэш для содержимого файла."""
    blob_header = f'blob {len(file_contents)}\0'
    full_blob = blob_header + file_contents
    return sha1(full_blob.encode('utf-8')).hexdigest()

def build_plantuml_graph(commits_per_tag: Dict[str, List[Tuple[str, str, str]]]) -> str:
    """Создать граф в формате PlantUML из коммитов."""
    plantuml_code = '@startuml\n'

    for tag, commits in commits_per_tag.items():
        plantuml_code += f'package "{tag}" {{\n'  # Создание пакета для каждого тега

        for idx, (commit_hash, commit_date, commit_author, commit_message) in enumerate(commits):
            plantuml_code += f'node "{commit_message}\\n{commit_date}\\n{commit_author}" as {tag}_{idx}\n'

        # Добавляем зависимости между коммитами внутри одного тега
        for i in range(len(commits) - 1):
            plantuml_code += f'{tag}_{i} --> {tag}_{i + 1}\n'

        plantuml_code += '}\n'  # Закрываем пакет для каждого тега

    plantuml_code += '@enduml'
    return plantuml_code

def visualize_graph(plantuml_code: str, visualization_tool: str):
    """Сохранить граф в файл и визуализировать его с помощью инструмента визуализации."""
    with open("graph.puml", "w") as f:
        f.write(plantuml_code)

    command = f"java -jar \"{visualization_tool}\" graph.puml"
    print(f"Visualizing graph with command: {command}")  # Отладочная информация
    result = subprocess.run(command, shell=True, capture_output=True)

    if result.returncode != 0:
        raise Exception(f"Error visualizing graph: {result.stderr.strip()}")

    os.remove("graph.puml")
    print("Граф зависимостей успешно сгенерирован!")

def get_commits_for_tags(repo_path: str, tag_names: List[str]) -> Dict[str, List[Tuple[str, str, str]]]:
    """Получить коммиты для всех указанных тегов."""
    commits_per_tag = {}
    previous_tag = None
    for tag_name in tag_names:
        tag_commits = get_commits(repo_path, tag_name, previous_tag)
        commits_per_tag[tag_name] = tag_commits
        previous_tag = tag_name  # Обновляем предыдущий тег
    return commits_per_tag

def main(config_path: str):
    """Основная функция для загрузки конфигурации, получения коммитов и визуализации графа."""
    config = load_config(config_path)
    print("Loaded config:", config)  # Отладочная информация
    
    commits_per_tag = get_commits_for_tags(config['repository_path'], config['tag_names'])
    
    print(f"Commits found: {commits_per_tag}")  # Отладочная информация
    plantuml_code = build_plantuml_graph(commits_per_tag)
    visualize_graph(plantuml_code, config['visualization_tool'])

if __name__ == "__main__":
    main("config.json")
