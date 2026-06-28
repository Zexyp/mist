from dataclasses import dataclass


@dataclass
class Artist:
    id: str
    name: str
    pass

@dataclass
class Track:
    id: str
    title: str
    pass