from enum import Enum


class OrderStatus(str, Enum):
    draft = "draft"
    published = "published"
    handling = "handling"
    done = "done"
    cancelled = "cancelled"


class VulnerabilityStatus(str, Enum):
    critical = "critical"
    major = "major"
    minor = "minor"
    clear = "clear"
    unknown = "unknown"


class FileType(str, Enum):
    img = "image"
    doc = "document"
