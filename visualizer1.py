import json
import os
import zlib
from hashlib import sha1
from typing import List, Dict, Tuple

def load_config(config_path: str) -> Dict[str, str]:
    """Загрузить конфигурацию из JSON файла."""
    with open(config_path, 'r') as f:
        return json.load(f)

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

def get_commit_data(repo_path: str, commit_hash: str) -> Tuple[str, str, str, str]:
    """Получить данные коммита: хеш, дата, автор, сообщение."""
    commit_data = read_git_object(repo_path, commit_hash)
    lines = commit_data.splitlines()
    author = ""
    date = ""
    message = []
    reading_message = False
    
    for line in lines:
        if line.startswith("author "):
            author_info = line.split("author ")[1]
            author, timestamp = author_info.rsplit(' ', 2)[0], author_info.rsplit(' ', 2)[1]
            date = timestamp
        elif not line:
            reading_message = True
        elif reading_message:
            message.append(line)
    
    return commit_hash, date, author, "\n".join(message)

def get_tag_commit(repo_path: str, tag_name: str) -> str:
    """Получить хеш коммита, связанный с указанным тегом."""
    tag_path = os.path.join(repo_path, '.git', 'refs', 'tags', tag_name)
    try:
        with open(tag_path, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        raise Exception(f"Tag {tag_name} not found.")

def get_commits_between(repo_path: str, start_hash: str, end_hash: str = None) -> List[Tuple[str, str, str, str]]:
    """Получить список коммитов между двумя хешами."""
    commits = []
    current_hash = start_hash

    while current_hash:
        commit_data = get_commit_data(repo_path, current_hash)
        commits.append(commit_data)
        
        # Получить родительский коммит
        commit_content = read_git_object(repo_path, current_hash)
        parent_line = next((line for line in commit_content.splitlines() if line.startswith("parent ")), None)
        
        if parent_line:
            current_hash = parent_line.split(" ")[1]
            if current_hash == end_hash:
                break
        else:
            break

    return commits[::-1]  # Возвращаем список в прямом порядке

def get_commits_for_tags(repo_path: str, tag_names: List[str]) -> Dict[str, List[Tuple[str, str, str, str]]]:
    """Получить коммиты для всех указанных тегов."""
    commits_per_tag = {}
    previous_commit = None
    for tag_name in tag_names:
        tag_commit = get_tag_commit(repo_path, tag_name)
        commits = get_commits_between(repo_path, tag_commit, previous_commit)
        commits_per_tag[tag_name] = commits
        previous_commit = tag_commit
    return commits_per_tag

def build_plantuml_graph(commits_per_tag: Dict[str, List[Tuple[str, str, str, str]]]) -> str:
    """Создать граф в формате PlantUML из коммитов."""
    plantuml_code = '@startuml\n'
    for tag, commits in commits_per_tag.items():
        plantuml_code += f'package "{tag}" {{\n'
        for idx, (commit_hash, commit_date, commit_author, commit_message) in enumerate(commits):
            plantuml_code += f'node "{commit_message}\\n{commit_date}\\n{commit_author}" as {tag}_{idx}\n'
        for i in range(len(commits) - 1):
            plantuml_code += f'{tag}_{i} --> {tag}_{i + 1}\n'
        plantuml_code += '}\n'
    plantuml_code += '@enduml'
    return plantuml_code

def visualize_graph(plantuml_code: str, visualization_tool: str):
    """Сохранить граф в файл и визуализировать его с помощью инструмента визуализации."""
    with open("graph.puml", "w") as f:
        f.write(plantuml_code)

    command = f"java -jar \"{visualization_tool}\" graph.puml"
    print(f"Visualizing graph with command: {command}")  # Отладочная информация
    result = os.system(command)

    if result != 0:
        raise Exception("Error visualizing graph.")
    os.remove("graph.puml")
    print("Граф зависимостей успешно сгенерирован!")

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
