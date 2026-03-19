from dataclasses import dataclass, field


@dataclass
class Control:
    id: str
    name: str
    description: str
    family: str
    weight: float = 1.0


@dataclass
class FrameworkDefinition:
    id: str
    name: str
    version: str
    controls: list[Control]
    family_weights: dict[str, float] = field(default_factory=dict)

    def get_families(self) -> list[str]:
        return list(dict.fromkeys(c.family for c in self.controls))

    def controls_by_family(self) -> dict[str, list[Control]]:
        result: dict[str, list[Control]] = {}
        for control in self.controls:
            result.setdefault(control.family, []).append(control)
        return result
