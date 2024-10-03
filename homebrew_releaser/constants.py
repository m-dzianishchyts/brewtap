import os


# Helper function to translate given INPUT_TARGET_* string from GitHub Actions into
# appropriate bool or string value.
def translate_target(target: str | bool) -> str | bool:
    if target is bool:
        return target
    target_url: str = str(target)
    if target_url.lower() not in {'true', 'false'}:
        return target
    else:
        return target_url.lower() == 'true'


# User Input
FORMULA_FOLDER = os.getenv('INPUT_FORMULA_FOLDER', 'formula')
GITHUB_TOKEN = os.getenv('INPUT_GITHUB_TOKEN')
HOMEBREW_TAP = os.getenv('INPUT_HOMEBREW_TAP')
SKIP_COMMIT = (
    os.getenv('INPUT_SKIP_COMMIT', False) if os.getenv('INPUT_SKIP_COMMIT') != 'false' else False
)  # Must check for string `false` since GitHub Actions passes the bool as a string
DOWNLOAD_STRATEGY = os.getenv('INPUT_DOWNLOAD_STRATEGY')
CUSTOM_REQUIRE = os.getenv('INPUT_CUSTOM_REQUIRE')
FORMULA_INCLUDES = os.getenv('INPUT_FORMULA_INCLUDES')
VERSION = os.getenv('INPUT_VERSION')

# App Constants
LOGGER_NAME = 'homebrew-releaser'
TIMEOUT = 30
GITHUB_HEADERS = {
    'Accept': 'application/vnd.github.v3+json',
    'Agent': 'Homebrew Releaser',
    'Authorization': f'Bearer {GITHUB_TOKEN}',
}
CHECKSUM_FILE = 'checksum.txt'

# GitHub Action env variables set by GitHub
GITHUB_REPOSITORY = os.getenv('GITHUB_REPOSITORY', 'user/repo').split('/')
GITHUB_OWNER = GITHUB_REPOSITORY[0]
GITHUB_REPO = GITHUB_REPOSITORY[1]

# Matrix targets to add URL/checksum targets for
TARGET = translate_target(os.getenv('INPUT_TARGET', False))
TARGET_DARWIN_AMD64 = translate_target(os.getenv('INPUT_TARGET_DARWIN_AMD64', False))
TARGET_DARWIN_ARM64 = translate_target(os.getenv('INPUT_TARGET_DARWIN_ARM64', False))
TARGET_LINUX_AMD64 = translate_target(os.getenv('INPUT_TARGET_LINUX_AMD64', False))
TARGET_LINUX_ARM64 = translate_target(os.getenv('INPUT_TARGET_LINUX_ARM64', False))
