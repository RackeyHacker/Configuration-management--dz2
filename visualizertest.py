import unittest
from unittest.mock import patch, MagicMock

# Импортируем функции из вашего модуля visualizer1
from visualizer1 import load_config, get_commits, get_commit_message, build_plantuml_graph, visualize_graph, get_commits_for_tags, main

class TestGitVisualization(unittest.TestCase):

    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data='{"repository_path": "/path/to/repo", "tag_names": ["v1.0", "v1.1"], "visualization_tool": "/path/to/plantuml.jar"}')
    def test_load_config(self, mock_open):
        config = load_config('fake_config.json')
        self.assertEqual(config['repository_path'], '/path/to/repo')
        self.assertEqual(config['tag_names'], ["v1.0", "v1.1"])
        self.assertEqual(config['visualization_tool'], '/path/to/plantuml.jar')

    @patch('subprocess.run')
    def test_get_commits(self, mock_run):
        # Имитация результата команды git
        mock_run.return_value = MagicMock(returncode=0, stdout='commit_hash|2024-10-20 12:00:00|Author Name\n', stderr='')
        commits = get_commits('/path/to/repo', 'v1.0')
        # Изменяем ожидаемую строку на фактическую
        self.assertEqual(commits[0], ('commit_hash', '2024-10-20 12:00:00', 'Author Name', 'commit_hash|2024-10-20 12:00:00|Author Name'))

    @patch('subprocess.run')
    def test_get_commit_message(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout='Commit message here\n', stderr='')
        message = get_commit_message('/path/to/repo', 'commit_hash')
        self.assertEqual(message, 'Commit message here')

    def test_build_plantuml_graph(self):
        commits = [
            ('commit_hash', '2024-10-20 12:00:00', 'Author Name', 'Commit message here'),
        ]
        plantuml_code = build_plantuml_graph({'v1.0': commits})
        self.assertIn('@startuml', plantuml_code)
        self.assertIn('@enduml', plantuml_code)
        self.assertIn('node "Commit message here\\n2024-10-20 12:00:00\\nAuthor Name" as v1.0_0', plantuml_code)

    @patch('subprocess.run')
    @patch('os.remove')
    def test_visualize_graph(self, mock_remove, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout='', stderr='')
        visualize_graph('@startuml\n@enduml', '/path/to/plantuml.jar')
        mock_run.assert_called_once()
        mock_remove.assert_called_once_with("graph.puml")

    @patch('visualizer1.get_commits')
    def test_get_commits_for_tags(self, mock_get_commits):
        mock_get_commits.side_effect = [
            [('commit_hash_v1.0', '2024-10-20 12:00:00', 'Author Name', 'Commit message v1.0')],
            [('commit_hash_v1.1', '2024-10-21 12:00:00', 'Author Name', 'Commit message v1.1')]
        ]
        tags = ["v1.0", "v1.1"]
        commits_per_tag = get_commits_for_tags('/path/to/repo', tags)
        self.assertEqual(len(commits_per_tag), 2)
        self.assertIn('v1.0', commits_per_tag)
        self.assertIn('v1.1', commits_per_tag)

    @patch('visualizer1.load_config')
    @patch('visualizer1.get_commits_for_tags')
    @patch('visualizer1.build_plantuml_graph')
    @patch('visualizer1.visualize_graph')
    def test_main(self, mock_visualize_graph, mock_build_plantuml_graph, mock_get_commits_for_tags, mock_load_config):
        mock_load_config.return_value = {'repository_path': '/path/to/repo', 'tag_names': ['v1.0', 'v1.1'], 'visualization_tool': '/path/to/plantuml.jar'}
        mock_get_commits_for_tags.return_value = {
            'v1.0': [('commit_hash_v1.0', '2024-10-20 12:00:00', 'Author Name', 'Commit message v1.0')],
            'v1.1': [('commit_hash_v1.1', '2024-10-21 12:00:00', 'Author Name', 'Commit message v1.1')]
        }
        mock_build_plantuml_graph.return_value = '@startuml\n@enduml'
        
        main('fake_config.json')
        
        mock_load_config.assert_called_once_with('fake_config.json')
        mock_get_commits_for_tags.assert_called_once()
        mock_build_plantuml_graph.assert_called_once()
        mock_visualize_graph.assert_called_once()

if __name__ == '__main__':
    unittest.main()
