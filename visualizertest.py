import unittest
from unittest.mock import patch, MagicMock

from visualizer1 import load_config, get_commits, get_commit_message, build_plantuml_graph, visualize_graph, get_commits_for_tags, main

class TestGitVisualization(unittest.TestCase):

    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data='{"repository_path": "/path/to/repo", "tag_names": ["v1.0", "v1.1"], "visualization_tool": "/path/to/plantuml.jar"}')
    def test_load_config(self, mock_open):
        # Тестирование функции load_config для загрузки конфигурации из файла
        config = load_config('fake_config.json')
        # Проверка, что значения загруженной конфигурации соответствуют ожидаемым
        self.assertEqual(config['repository_path'], '/path/to/repo')
        self.assertEqual(config['tag_names'], ["v1.0", "v1.1"])
        self.assertEqual(config['visualization_tool'], '/path/to/plantuml.jar')

    @patch('subprocess.run')
    def test_get_commits(self, mock_run):
        # Тестирование функции get_commits для получения коммитов из репозитория
        # Имитация результата выполнения команды git
        mock_run.return_value = MagicMock(returncode=0, stdout='commit_hash|2024-10-20 12:00:00|Author Name\n', stderr='')
        commits = get_commits('/path/to/repo', 'v1.0')
        # Проверка, что полученные коммиты соответствуют ожидаемым
        self.assertEqual(commits[0], ('commit_hash', '2024-10-20 12:00:00', 'Author Name', 'commit_hash|2024-10-20 12:00:00|Author Name'))

    @patch('subprocess.run')
    def test_get_commit_message(self, mock_run):
        # Тестирование функции get_commit_message для получения сообщения коммита
        mock_run.return_value = MagicMock(returncode=0, stdout='Commit message here\n', stderr='')
        message = get_commit_message('/path/to/repo', 'commit_hash')
        # Проверка, что полученное сообщение соответствует ожидаемому
        self.assertEqual(message, 'Commit message here')

    def test_build_plantuml_graph(self):
        # Тестирование функции build_plantuml_graph для построения графа PlantUML
        commits = [
            ('commit_hash', '2024-10-20 12:00:00', 'Author Name', 'Commit message here'),
        ]
        plantuml_code = build_plantuml_graph({'v1.0': commits})
        # Проверка наличия необходимых частей в коде PlantUML
        self.assertIn('@startuml', plantuml_code)
        self.assertIn('@enduml', plantuml_code)
        self.assertIn('node "Commit message here\\n2024-10-20 12:00:00\\nAuthor Name" as v1.0_0', plantuml_code)

    @patch('subprocess.run')
    @patch('os.remove')
    def test_visualize_graph(self, mock_remove, mock_run):
        # Тестирование функции visualize_graph для визуализации графа
        mock_run.return_value = MagicMock(returncode=0, stdout='', stderr='')
        visualize_graph('@startuml\n@enduml', '/path/to/plantuml.jar')
        # Проверка, что команда визуализации была вызвана и временный файл был удален
        mock_run.assert_called_once()
        mock_remove.assert_called_once_with("graph.puml")

    @patch('visualizer1.get_commits')
    def test_get_commits_for_tags(self, mock_get_commits):
        # Тестирование функции get_commits_for_tags для получения коммитов по тегам
        mock_get_commits.side_effect = [
            [('commit_hash_v1.0', '2024-10-20 12:00:00', 'Author Name', 'Commit message v1.0')],
            [('commit_hash_v1.1', '2024-10-21 12:00:00', 'Author Name', 'Commit message v1.1')]
        ]
        tags = ["v1.0", "v1.1"]
        commits_per_tag = get_commits_for_tags('/path/to/repo', tags)
        # Проверка, что количество тегов и их наличие в результате соответствуют ожиданиям
        self.assertEqual(len(commits_per_tag), 2)
        self.assertIn('v1.0', commits_per_tag)
        self.assertIn('v1.1', commits_per_tag)

    @patch('visualizer1.load_config')
    @patch('visualizer1.get_commits_for_tags')
    @patch('visualizer1.build_plantuml_graph')
    @patch('visualizer1.visualize_graph')
    def test_main(self, mock_visualize_graph, mock_build_plantuml_graph, mock_get_commits_for_tags, mock_load_config):
        # Тестирование основной функции main для проверки всего процесса
        mock_load_config.return_value = {'repository_path': '/path/to/repo', 'tag_names': ['v1.0', 'v1.1'], 'visualization_tool': '/path/to/plantuml.jar'}
        mock_get_commits_for_tags.return_value = {
            'v1.0': [('commit_hash_v1.0', '2024-10-20 12:00:00', 'Author Name', 'Commit message v1.0')],
            'v1.1': [('commit_hash_v1.1', '2024-10-21 12:00:00', 'Author Name', 'Commit message v1.1')]
        }
        mock_build_plantuml_graph.return_value = '@startuml\n@enduml'
        
        main('fake_config.json')
        
        # Проверка, что все функции были вызваны с правильными параметрами
        mock_load_config.assert_called_once_with('fake_config.json')
        mock_get_commits_for_tags.assert_called_once()
        mock_build_plantuml_graph.assert_called_once()
        mock_visualize_graph.assert_called_once()

if __name__ == '__main__':
    unittest.main()
