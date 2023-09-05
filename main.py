"""Semantic Version Bumper"""

from re import match, Match
from os import getcwd, getenv
from typing import Final, Optional
from git import Repo, InvalidGitRepositoryError, NoSuchPathError, TagReference
from semver import Version


DEFAULT_GIT_PATH: Final = getenv(key='GIT_PATH', default=getcwd())
DEFAULT_NO_RELEASE_BUMP: Final = \
    getenv(key='NO_RELEASE_BUMP', default='norelease')


def get_repo(path=DEFAULT_GIT_PATH) -> Repo:
    """Get git repository instance"""
    try:
        repo: Repo = Repo(path=path)
        return repo
    except InvalidGitRepositoryError as exc:
        raise InvalidGitRepositoryError(f"Invalid git repository '{path}'") \
            from exc
    except NoSuchPathError as exc:
        raise NoSuchPathError(f"No such path '{path}'") from exc


def get_commits(repo: Repo, tag: Optional[str] = None) -> list[str]:
    """Get git commit messages"""
    rev: str | None = None if tag is None else f'{tag}..HEAD'
    return [commit.message.strip() for commit in repo.iter_commits(rev=rev)]


def detect_release_type(commits: list[str]) -> Optional[str]:
    """Detect release type using given commit messages"""
    patch: int = 0
    minor: int = 0
    major: int = 0

    for commit in commits:
        if commit.startswith('fixup!'):
            continue
        matches: Optional[Match[str]] = \
            match(pattern=r'^(.*):(.*)$',
                  string=commit.replace('\n', ''))
        if matches is None:
            continue
        type_scope, _ = matches.groups()
        if 'BREAKING CHANGE:' in commit or type_scope.endswith('!'):
            major += 1
        elif type_scope.startswith('feat'):
            minor += 1
        elif type_scope.startswith('fix'):
            patch += 1

    if major > 0:
        return 'major'
    if minor > 0:
        return 'minor'
    if patch > 0:
        return 'patch'
    return None


def bump_version(version: Version, release_type: Optional[str]) -> Version:
    """Bump semantic version using release type"""
    if release_type == 'patch' or \
            (release_type is None and DEFAULT_NO_RELEASE_BUMP == 'patch'):
        return version.bump_patch()
    if release_type == 'minor' or \
            (release_type is None and DEFAULT_NO_RELEASE_BUMP == 'minor'):
        return version.bump_minor()
    if release_type == 'major' or \
            (release_type is None and DEFAULT_NO_RELEASE_BUMP == 'major'):
        return version.bump_major()
    return version


def get_last_tag(repo: Repo) -> Optional[str]:
    """Get last tag"""
    sorted_tags: list[TagReference] = \
        sorted(repo.tags, key=lambda t: t.commit.committed_datetime)
    if not sorted_tags:
        return None
    return str(sorted_tags.pop()).split('/').pop()


def get_last_version(tag: Optional[str]) -> Version:
    """Get last version using tag"""
    if tag is None:
        return Version(major=0)
    return Version.parse(version=tag.lstrip('v'))


def main() -> None:  # pragma: no cover
    """Main method"""
    repo: Repo = get_repo()
    last_tag: str = get_last_tag(repo=repo)
    my_semver: Version = get_last_version(tag=last_tag)
    try:
        commits: list[str] = get_commits(repo=repo, tag=last_tag)
        release_type = detect_release_type(commits=commits)
        new_version = \
            bump_version(version=my_semver, release_type=release_type)
        print(new_version)
    except Exception as exc:
        raise ValueError('Bump semantic version failed') from exc


if __name__ == '__main__':  # pragma: no cover
    main()
