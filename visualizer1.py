import json
import subprocess
import os
from typing import List, Dict, Tuple

def load_config(config_path: str) -> Dict[str, str]:
    with open(config_path, 'r') as f:
        return json.load(f)

def get_commits(repo_path: str, tag_name: str, previous_tag: str = None) -> List[Tuple[str, str, str]]:
    if previous_tag:
        # Получить коммиты между предыдущим тегом и текущим тегом
        command = f'git -C "{repo_path}" log "{previous_tag}..{tag_name}" --pretty=format:"%H|%ad|%an" --date=iso'
    else:
        # Получить все коммиты до данного тега (если предыдущего тега нет)
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
    command = f'git -C "{repo_path}" log -1 --pretty=%B {commit_hash}'
    result = subprocess.run(command, shell=True, text=True, capture_output=True)
    if result.returncode != 0:
        raise Exception(f"Error getting commit message: {result.stderr.strip()}")
    return result.stdout.strip()

def build_plantuml_graph(commits_per_tag: Dict[str, List[Tuple[str, str, str]]]) -> str:
    plantuml_code = '@startuml\n'

    for tag, commits in commits_per_tag.items():
        plantuml_code += f'package "{tag}" {{\n'  # Создание пакета для каждого тега

        # Добавляем пространство для каждого тега
        for idx, (commit_hash, commit_date, commit_author, commit_message) in enumerate(commits):
            # Включаем сообщение коммита, дату и автора
            plantuml_code += f'node "{commit_message}\\n{commit_date}\\n{commit_author}" as {tag}_{idx}\n'

        # Добавляем зависимости между коммитами внутри одного тега
        for i in range(len(commits) - 1):
            plantuml_code += f'{tag}_{i} --> {tag}_{i + 1}\n'

        plantuml_code += '}\n'  # Закрываем пакет для каждого тега

    plantuml_code += '@enduml'
    return plantuml_code

def visualize_graph(plantuml_code: str, visualization_tool: str):
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
    commits_per_tag = {}
    previous_tag = None
    for tag_name in tag_names:
        tag_commits = get_commits(repo_path, tag_name, previous_tag)
        commits_per_tag[tag_name] = tag_commits
        previous_tag = tag_name  # Обновляем предыдущий тег
    return commits_per_tag

def main(config_path: str):
    config = load_config(config_path)
    print("Loaded config:", config)  # Отладочная информация
    
    commits_per_tag = get_commits_for_tags(config['repository_path'], config['tag_names'])
    
    print(f"Commits found: {commits_per_tag}")  # Отладочная информация
    plantuml_code = build_plantuml_graph(commits_per_tag)
    visualize_graph(plantuml_code, config['visualization_tool'])

if __name__ == "__main__":
    main("config.json")
