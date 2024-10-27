import unittest
from unittest.mock import patch, mock_open, MagicMock
import json

from visualizer1 import (
    load_config,
    read_git_object,
    get_commit_data,
    get_tag_commit,
    get_commits_between,
    get_commits_for_tags,
    build_plantuml_graph,
    visualize_graph
)

class TestGitFunctions(unittest.TestCase):

    @patch('builtins.open', new_callable=mock_open, read_data='{"repository_path": "/path/to/repo", "tag_names": ["v1.0"], "visualization_tool": "tool.jar"}')
    def test_load_config(self, mock_file):
        config = load_config("dummy_path.json")
        self.assertEqual(config['repository_path'], '/path/to/repo')
        self.assertIn('tag_names', config)
        self.assertIsInstance(config['tag_names'], list)

    @patch('os.path.join', return_value='dummy/path/to/git/object')
    @patch('builtins.open', new_callable=mock_open, read_data=b'x\x9c+\xce\xc8\xcd+\xd0\x03\x00\x02\x18\x01\x0b')
    def test_read_git_object(self, mock_file, mock_join):
        result = read_git_object('dummy/repo/path', 'dummyhash')
        self.assertEqual(result, 'Hello World\n')

    @patch('visualizer1.read_git_object', return_value='commit hash\nauthor John Doe <john@example.com> 1617984296\n\nInitial commit')
    def test_get_commit_data(self, mock_read_git_object):
        commit_data = get_commit_data('dummy/repo/path', 'dummy_commit_hash')
        self.assertEqual(commit_data[0], 'dummy_commit_hash')
        self.assertEqual(commit_data[1], '1617984296')
        self.assertEqual(commit_data[2], 'John Doe')
        self.assertEqual(commit_data[3], 'Initial commit')

    @patch('builtins.open', new_callable=mock_open, read_data='dummy_commit_hash')
    def test_get_tag_commit(self, mock_file):
        tag_commit = get_tag_commit('dummy/repo/path', 'v1.0')
        self.assertEqual(tag_commit, 'dummy_commit_hash')

    @patch('visualizer1.get_commit_data', side_effect=[
        ('hash1', 'date1', 'author1', 'message1'),
        ('hash2', 'date2', 'author2', 'message2')
    ])
    def test_get_commits_between(self, mock_get_commit_data):
        commits = get_commits_between('dummy/repo/path', 'start_hash', 'end_hash')
        self.assertEqual(len(commits), 2)
        self.assertEqual(commits[0], ('hash1', 'date1', 'author1', 'message1'))
        self.assertEqual(commits[1], ('hash2', 'date2', 'author2', 'message2'))

    def test_build_plantuml_graph(self):
        commits_per_tag = {
            'v1.0': [
                ('hash1', 'date1', 'author1', 'message1'),
                ('hash2', 'date2', 'author2', 'message2')
            ]
        }
        plantuml_code = build_plantuml_graph(commits_per_tag)
        self.assertIn('@startuml', plantuml_code)
        self.assertIn('@enduml', plantuml_code)
        self.assertIn('node "message1\\ndate1\\nauthor1"', plantuml_code)
        self.assertIn('node "message2\\ndate2\\nauthor2"', plantuml_code)
        self.assertIn('v1.0', plantuml_code)

    @patch('builtins.open', new_callable=mock_open)
    @patch('os.system', return_value=0)
    def test_visualize_graph(self, mock_system, mock_file):
        visualize_graph('dummy_plantuml_code', 'dummy_tool.jar')
        mock_file.assert_called_once_with("graph.puml", "w")
        mock_system.assert_called_once_with('java -jar "dummy_tool.jar" graph.puml')

if __name__ == '__main__':
    unittest.main()
