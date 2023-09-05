"""Semantic Version Bumper Tests"""

from random import choice
from pathlib import Path
from unittest import TestCase
from tempfile import TemporaryDirectory
from git import Repo, Actor, NoSuchPathError, InvalidGitRepositoryError
from semver import Version
from main import detect_release_type, \
                 bump_version, \
                 get_commits, \
                 get_last_version, \
                 get_last_tag, \
                 get_repo


class Test(TestCase):
    """Semantic Version Bumper Test Cases"""

    def test_detect_release_type(self):
        """Test detect_release_type()"""
        breaking_commits: list[str] = [
            'feat!: use Docker multi-stage build',
            'feat(api)!: send an email to the customer when a product is '
            'shipped',
            'feat: allow provided config object to extend other configs\n\n'
            'BREAKING CHANGE: `extends` key in config file is now used for '
            'extending other config files',
            'fix!: upgrade copyparty to version 1.8.7 (CVE-2023-38501)'
        ]
        feat_commit: str = 'feat: use Docker multi-stage build'
        fix_commit: str = ('fix: upgrade copyparty to version 1.8.7 '
                           '(CVE-2023-38501)')
        ci_commit: str = 'ci: enable verbose mode while running pytest'
        invalid_commit: str = ('Introduce a request id and a reference to '
                               'latest request')
        fixup_commit: str = 'fixup! feat!: use Docker multi-stage build'

        # Breaking/Major Release
        self.assertEqual(
            first=detect_release_type(commits=[
                feat_commit,
                choice(seq=breaking_commits),
                fix_commit,
                ci_commit
            ]),
            second='major'
        )

        # Minor Release
        self.assertEqual(
            first=detect_release_type(commits=[
                feat_commit,
                fix_commit,
                ci_commit
            ]),
            second='minor'
        )

        # Patch Release
        self.assertEqual(
            first=detect_release_type(commits=[fix_commit, ci_commit]),
            second='patch'
        )

        # No Release
        self.assertIsNone(obj=detect_release_type(commits=[ci_commit]))
        self.assertIsNone(obj=detect_release_type(commits=[invalid_commit]))
        self.assertIsNone(obj=detect_release_type(commits=[fixup_commit]))

    def test_bump_version(self):
        """Test bump_version()"""
        my_semver: Version = Version(major=0, minor=3, patch=7)

        # Major
        self.assertEqual(
            first=bump_version(version=my_semver, release_type='major'),
            second=Version(major=1, minor=0, patch=0)
        )

        # Minor
        self.assertEqual(
            first=bump_version(version=my_semver, release_type='minor'),
            second=Version(major=0, minor=4, patch=0)
        )

        # Patch
        self.assertEqual(
            first=bump_version(version=my_semver, release_type='patch'),
            second=Version(major=0, minor=3, patch=8)
        )

        # None
        self.assertEqual(
            first=bump_version(version=my_semver, release_type=None),
            second=Version(major=0, minor=3, patch=7)
        )

    def test_get_repo(self):
        """Test get_repo()"""
        # Test invalid git repository
        with self.assertRaises(expected_exception=InvalidGitRepositoryError):
            get_repo(path='/tmp')

        # Test no such path
        with self.assertRaises(expected_exception=NoSuchPathError):
            get_repo(path='/toto')

        with TemporaryDirectory() as tmpdirname:
            Repo.init(path=tmpdirname, initial_branch='main')
            self.assertIsInstance(obj=get_repo(path=tmpdirname), cls=Repo)

    def test_get_commits(self):
        """Test get_commits()"""
        with TemporaryDirectory() as tmpdirname:
            committer: Actor = Actor(name='Jonathan Sabbe',
                                     email='jonathan.sabbe@speos.be')
            repo: Repo = Repo.init(path=tmpdirname, initial_branch='main')
            readme_file: str = f'{tmpdirname}/README.md'
            Path(readme_file).touch()
            repo.index.add(items=[readme_file])
            repo.index.commit(message="feat: initial commit",
                              committer=committer)

            commits: list[str] = get_commits(repo=repo)
            release_type: str = detect_release_type(commits=commits)
            my_semver: Version = Version(major=0)

            # Test Commits
            self.assertEqual(
                first=commits,
                second=["feat: initial commit"]
            )

            # Test Release Type
            self.assertEqual(
                first=release_type,
                second='minor'
            )

            # Test Semantic Versioning
            self.assertEqual(
                first=bump_version(version=my_semver,
                                   release_type=release_type),
                second=Version(major=0, minor=1)
            )

    def test_get_last_version(self):
        """Test get_last_version()"""
        self.assertEqual(first=get_last_version(tag='v1.2.3'),
                         second=Version(major=1, minor=2, patch=3))
        self.assertEqual(first=get_last_version(tag=None),
                         second=Version(major=0))

    def test_get_last_tag(self):
        """Test get_last_tag()"""
        with TemporaryDirectory() as tmpdirname:
            committer: Actor = Actor(name='Jonathan Sabbe',
                                     email='jonathan.sabbe@speos.be')
            repo: Repo = Repo.init(path=tmpdirname, initial_branch='main')
            readme_file: str = f'{tmpdirname}/README.md'
            Path(readme_file).touch()
            repo.index.add(items=[readme_file])
            repo.index.commit(message="feat: initial commit",
                              committer=committer)
            self.assertIsNone(obj=get_last_tag(repo=repo))
            repo.create_tag(path='v0.1.0')
            self.assertEqual(first=get_last_tag(repo=repo), second='v0.1.0')
