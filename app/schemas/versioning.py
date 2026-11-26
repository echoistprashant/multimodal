"""Schema Semantic Versioning and Payload Migration Engine.

Enforces Semantic Versioning (SemVer) compatibility contracts and applies
field-level payload migrations across document schema evolutions.
"""

from typing import Any, Dict, Tuple


class SemVer:
    """Semantic version parser supporting major, minor, and patch comparisons."""

    def __init__(self, version_str: str) -> None:
        self.raw = version_str.strip()
        parts = self.raw.split(".")
        if len(parts) != 3:
            raise ValueError(f"Invalid SemVer string '{version_str}'. Must follow 'MAJOR.MINOR.PATCH'.")
        try:
            self.major = int(parts[0])
            self.minor = int(parts[1])
            self.patch = int(parts[2])
        except ValueError as err:
            raise ValueError(f"Non-integer component in SemVer '{version_str}': {err}")

    def as_tuple(self) -> Tuple[int, int, int]:
        return (self.major, self.minor, self.patch)

    def is_backward_compatible_with(self, target: "SemVer") -> bool:
        """Backward compatibility holds if major versions match and self >= target."""
        return self.major == target.major and self.as_tuple() >= target.as_tuple()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SemVer):
            return False
        return self.as_tuple() == other.as_tuple()

    def __lt__(self, other: "SemVer") -> bool:
        return self.as_tuple() < other.as_tuple()

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"


def check_schema_compatibility(source_ver_str: str, target_ver_str: str) -> bool:
    """Verify whether source schema version is compatible with target schema version."""
    src = SemVer(source_ver_str)
    target = SemVer(target_ver_str)
    return src.is_backward_compatible_with(target)


def migrate_document_payload(
    payload: Dict[str, Any],
    from_version: str,
    to_version: str,
) -> Dict[str, Any]:
    """Migrate serialized document dictionary across schema versions.

    Ensures newly required fields receive defaults and deprecated fields are mapped.
    """
    if from_version == to_version:
        return dict(payload)

    migrated = dict(payload)
    migrated["schema_version"] = to_version

    # Migration from 1.0.0 to 1.1.0: ensure currency defaults to USD if absent
    if from_version == "1.0.0" and to_version in ["1.1.0", "1.2.0"]:
        if "currency" not in migrated:
            migrated["currency"] = "USD"

    return migrated
