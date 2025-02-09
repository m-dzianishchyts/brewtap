import os
from typing import Optional

import woodchips

from brewtap._version import __version__
from brewtap.checksum import Checksum
from brewtap.constants import (
    CAVEATS,
    CHECKSUM_FILE,
    COMMIT_EMAIL,
    COMMIT_OWNER,
    CUSTOM_REQUIRE,
    DEBUG,
    DEPENDS_ON,
    DOWNLOAD_STRATEGY,
    FORMULA_FOLDER,
    FORMULA_INCLUDES,
    GITHUB_BASE_URL,
    GITHUB_OWNER,
    GITHUB_REPO,
    GITHUB_TOKEN,
    HOMEBREW_OWNER,
    HOMEBREW_TAP,
    INSTALL,
    LOGGER_NAME,
    SKIP_COMMIT,
    TARGET,
    TARGET_DARWIN_AMD64,
    TARGET_DARWIN_ARM64,
    TARGET_LINUX_AMD64,
    TARGET_LINUX_ARM64,
    TEST,
    UPDATE_README_TABLE,
    VERSION,
)
from brewtap.formula import Formula
from brewtap.git import Git
from brewtap.readme_updater import ReadmeUpdater
from brewtap.utils import Utils


class App:
    @staticmethod
    def run_github_action():
        """Runs the complete GitHub Action workflow.

        1. Setup logging
        2. Grab the details about the tap
        3. Download the archive(s)
        4. Generate checksum(s)
        5. Generate the new formula
        6. Update README table (optional)
        7. Add, commit, and push updated formula to GitHub
        """
        App.setup_logger()
        logger = woodchips.get(LOGGER_NAME)

        logger.info(f'Starting Brewtap {__version__}...')
        App.check_required_env_variables()

        logger.info('Setting up git environment...')
        Git.setup(COMMIT_OWNER, COMMIT_EMAIL, HOMEBREW_OWNER, HOMEBREW_TAP)

        logger.info(f'Collecting data about {GITHUB_REPO}...')
        repository = Utils.make_github_get_request(url=f'{GITHUB_BASE_URL}/repos/{GITHUB_OWNER}/{GITHUB_REPO}').json()
        release = Utils.make_github_get_request(
            url=f'https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/{f"tags/{VERSION}" if VERSION else 'latest'}'  # noqa
        ).json()
        assets = release['assets']
        version = VERSION or release['tag_name']
        version_no_v = version.lstrip('v')
        logger.info(f'Latest release ({version}) successfully identified!')

        logger.info('Generating tar archive checksum(s)...')
        archive_urls = dict()
        archive_checksum_entries = ''

        # Auto-generated tar URL must come first for later use (order is important)
        if repository["private"]:
            logger.info('Repository is private. Using auto-generated release tarball and zipball REST API endpoints.')
            archive_base_url = f'{GITHUB_BASE_URL}/repos/{GITHUB_OWNER}/{GITHUB_REPO}'
            auto_generated_release_tar = f'{archive_base_url}/tarball/{version}'
            auto_generated_release_zip = f'{archive_base_url}/zipball/{version}'
        else:
            logger.info('Repository is public. Using auto-generated release tarball and zipball public URLs.')
            archive_base_url = f'https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/archive/refs/tags/{version}'
            auto_generated_release_tar = f'{archive_base_url}.tar.gz'
            auto_generated_release_zip = f'{archive_base_url}.zip'

        archive_urls['default'] = auto_generated_release_tar

        target_browser_download_base_url = (
            f'https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/releases/download/{version}/'
        )
        default_target_prefix = f'{GITHUB_REPO}-{version_no_v}'
        if isinstance(TARGET, str):
            archive_urls['default'] = f'{target_browser_download_base_url}{TARGET}'
            logger.debug('Target overridden (default): %s', archive_urls['default'])
        if TARGET_DARWIN_AMD64:
            archive_urls['darwin_amd64'] = (
                f'{target_browser_download_base_url}{(
                    TARGET_DARWIN_AMD64 if isinstance(TARGET_DARWIN_AMD64, str)
                    else f'{default_target_prefix}-darwin-amd64.tar.gz'
                )}'
            )
            logger.debug('Target overridden (darwin_amd64): %s', archive_urls['darwin_amd64'])
        if TARGET_DARWIN_ARM64:
            archive_urls['darwin_arm64'] = (
                f'{target_browser_download_base_url}{(
                    TARGET_DARWIN_ARM64 if isinstance(TARGET_DARWIN_ARM64, str)
                    else f'{default_target_prefix}-darwin-arm64.tar.gz'
                )}'
            )
            logger.debug('Target overridden (darwin_arm64): %s', archive_urls['darwin_arm64'])
        if TARGET_LINUX_AMD64:
            archive_urls['linux_amd64'] = (
                f'{target_browser_download_base_url}{(
                    TARGET_LINUX_AMD64 if isinstance(TARGET_LINUX_AMD64, str)
                    else f'{default_target_prefix}-linux-amd64.tar.gz'
                )}'
            )
            logger.debug('Target overridden (linux_amd64): %s', archive_urls['linux_amd64'])
        if TARGET_LINUX_ARM64:
            archive_urls['linux_arm64'] = (
                f'{target_browser_download_base_url}{(
                    TARGET_LINUX_ARM64 if isinstance(TARGET_LINUX_ARM64, str)
                    else f'{default_target_prefix}-linux-arm64.tar.gz'
                )}'
            )
            logger.debug('Target overridden (linux_arm64): %s', archive_urls['linux_arm64'])

        checksums = []
        for archive_type, archive_url in archive_urls.items():
            if not assets:
                assets = [0]  # TODO: This is a dumb hack to ensure we enter here even when we don't have any assets
            for asset in assets:
                # Download the asset url so private repos work but use the brower URL for name and path in formula
                if archive_url == auto_generated_release_tar or archive_url == auto_generated_release_zip:
                    download_url = archive_url
                else:
                    download_url = asset['url']

                if (
                    archive_url == auto_generated_release_tar
                    or archive_url == auto_generated_release_zip
                    or archive_url == asset['browser_download_url']
                ):
                    # For REST API requests, we should not stream archive file, but it is fine for browser URLs
                    stream = False if archive_url.find("api.github.com") != -1 else True
                    downloaded_filename = App.download_archive(download_url, stream)
                    checksum = Checksum.get_checksum(downloaded_filename)
                    archive_filename = Utils.get_filename_from_path(archive_url)
                    archive_checksum_entries += f'{checksum} {archive_filename}\n'
                    checksums.append(
                        {archive_filename: {'checksum': checksum, 'url': archive_url, 'type': archive_type}},
                    )
                    break

        logger.debug("checksums = %s", checksums)
        Utils.write_file(CHECKSUM_FILE, archive_checksum_entries)

        logger.info(f'Generating Homebrew formula for {GITHUB_REPO}...')
        template = Formula.generate_formula_data(
            owner=GITHUB_OWNER,
            repo_name=GITHUB_REPO,
            repository=repository,
            checksums=checksums,
            install=INSTALL,
            tar_url=archive_urls['default'],
            depends_on=DEPENDS_ON,
            test=TEST,
            caveats=CAVEATS,
            download_strategy=DOWNLOAD_STRATEGY,
            custom_require=CUSTOM_REQUIRE,
            formula_includes=FORMULA_INCLUDES,
            version=version_no_v if VERSION else None,
        )

        Utils.write_file(os.path.join(HOMEBREW_TAP, FORMULA_FOLDER, f'{repository["name"]}.rb'), template, 'w')

        if UPDATE_README_TABLE:
            logger.info('Attempting to update the README\'s project table...')
            ReadmeUpdater.update_readme(HOMEBREW_TAP)
        else:
            logger.debug('Skipping update to project README.')

        # Although users can skip a commit, still commit (and don't push) to dry-run a commit
        Git.add(HOMEBREW_TAP)
        Git.commit(HOMEBREW_TAP, GITHUB_REPO, version)

        if SKIP_COMMIT:
            logger.info(f'Skipping upload of checksum.txt to {HOMEBREW_TAP}.')
            logger.info(f'Skipping push to {HOMEBREW_TAP}.')
        else:
            logger.info(f'Attempting to upload checksum.txt to the latest release of {GITHUB_REPO}...')
            Checksum.upload_checksum_file(release)
            logger.info(f'Attempting to release {version} of {GITHUB_REPO} to {HOMEBREW_TAP}...')
            Git.push(HOMEBREW_TAP, HOMEBREW_OWNER)
            logger.info(f'Successfully released {version} of {GITHUB_REPO} to {HOMEBREW_TAP}!')

    @staticmethod
    def setup_logger():
        """Setup a `woodchips` logger instance."""
        logging_level = 'DEBUG' if DEBUG else 'INFO'

        logger = woodchips.Logger(
            name=LOGGER_NAME,
            level=logging_level,
        )
        logger.log_to_console(formatter='%(asctime)s - %(levelname)s - %(message)s')

    @staticmethod
    def check_required_env_variables():
        """Checks that all required env variables are set."""
        logger = woodchips.get(LOGGER_NAME)

        required_env_variables = [
            GITHUB_TOKEN,
            HOMEBREW_OWNER,
            HOMEBREW_TAP,
            INSTALL,
        ]

        for env_variable in required_env_variables:
            if not env_variable:
                raise SystemExit(
                    'You must provide all necessary environment variables. Please reference the Brewtap documentation.'  # noqa
                )
        logger.debug('All required environment variables are present.')

    @staticmethod
    def download_archive(url: str, stream: Optional[bool] = False) -> str:
        """Gets an archive (eg: zip, tar) from GitHub and saves it locally."""
        response = Utils.make_github_get_request(
            url=url,
            stream=stream,
        )
        filename = Utils.get_filename_from_path(url)
        Utils.write_file(filename, response.content, 'wb')

        return filename


def main():
    App.run_github_action()


if __name__ == '__main__':
    main()
