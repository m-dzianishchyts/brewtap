import subprocess  # nosec
from typing import Any

import requests
import woodchips

from brewtap.constants import (
    CHECKSUM_FILE,
    GITHUB_HEADERS,
    GITHUB_OWNER,
    GITHUB_REPO,
    LOGGER_NAME,
    TIMEOUT,
)


class Checksum:
    @staticmethod
    def get_checksum(tar_filepath: str) -> str:
        """Gets the checksum of a file."""
        logger = woodchips.get(LOGGER_NAME)

        try:
            command = ['shasum', '-a', '256', tar_filepath]
            output = subprocess.check_output(  # nosec
                command,
                stdin=None,
                stderr=None,
                timeout=TIMEOUT,
            )
            checksum = output.decode().split()[0]
            checksum_filename = output.decode().split()[1]
            logger.debug(f'Checksum for {checksum_filename} generated successfully: {checksum}')
        except subprocess.TimeoutExpired as error:
            raise SystemExit(error)
        except subprocess.CalledProcessError as error:
            raise SystemExit(error)

        return checksum

    @staticmethod
    def upload_checksum_file(release: dict[str, Any]):
        """Uploads a `checksum.txt` file to the latest release of the repo."""
        logger = woodchips.get(LOGGER_NAME)

        release_id = release['id']

        with open(CHECKSUM_FILE, 'rb') as filename:
            checksum_binary = filename.read()

        upload_url = f'https://uploads.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/{release_id}/assets?name={CHECKSUM_FILE}'  # noqa
        headers = GITHUB_HEADERS.copy()
        headers['Content-Type'] = 'text/plain'

        try:
            response = requests.post(
                upload_url,
                headers=headers,
                data=checksum_binary,
                timeout=TIMEOUT,
            )
            if response.ok:
                logger.info(f'checksum.txt uploaded successfully to {GITHUB_REPO}.')
            else:
                logger.debug(response.json())
                SystemExit(f'checksum.txt was not uploaded: received status code ${response.status_code}')
        except requests.exceptions.RequestException as error:
            raise SystemExit(error)
