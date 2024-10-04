import os
from unittest.mock import patch

from brewtap.app import App


@patch.dict(os.environ, {'INPUT_SKIP_COMMIT': 'false'})
@patch.dict(os.environ, {'INPUT_SKIP_COMMIT': 'false'})
@patch('brewtap.readme_updater.ReadmeUpdater.update_readme')
@patch('brewtap.checksum.Checksum.upload_checksum_file')
@patch('brewtap.app.HOMEBREW_TAP', '123')
@patch('woodchips.get')
@patch('brewtap.git.Git.setup')
@patch('brewtap.git.Git.add')
@patch('brewtap.git.Git.commit')
@patch('brewtap.git.Git.push')
@patch('brewtap.utils.Utils.write_file')
@patch('brewtap.formula.Formula.generate_formula_data')
@patch('brewtap.checksum.Checksum.get_checksum', return_value=('123', 'mock-repo'))
@patch('brewtap.app.App.download_archive')
@patch('brewtap.utils.Utils.make_github_get_request')
@patch('brewtap.app.App.check_required_env_variables')
def test_run_github_action_string_false_config(
    mock_check_env_variables,
    mock_make_github_get_request,
    mock_download_archive,
    mock_get_checksum,
    mock_generate_formula,
    mock_write_file,
    mock_push_formula,
    mock_commit_formula,
    mock_add_formula,
    mock_setup_git,
    mock_logger,
    mock_upload_checksum_file,
    mock_update_readme,
):
    App.run_github_action()

    # Check that string false works by running git operations
    mock_add_formula.assert_called_once()
    mock_commit_formula.assert_called_once()
    mock_push_formula.assert_called_once()

    # Check that we don't update the README with a string false
    mock_update_readme.assert_not_called()
