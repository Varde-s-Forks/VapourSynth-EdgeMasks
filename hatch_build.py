import sysconfig
from functools import cache
from typing import Any

from hatchling.builders.hooks.plugin.interface import BuildHookInterface
from hatchling.builders.wheel import WheelBuilderConfig
from hatchling.metadata.plugin.interface import MetadataHookInterface

_ARTIFACTS = {
    "windows": "edgemasks.dll",
    "linux": "edgemasks.so",
    "macos": "edgemasks.dylib",
}

_PLUGIN_NAMESPACE = "edgemasks"


@cache
def get_artifact_name() -> str:
    platform = sysconfig.get_platform()

    if platform.startswith("win"):
        return _ARTIFACTS["windows"]

    if platform.startswith("linux"):
        return _ARTIFACTS["linux"]

    if platform == "darwin":
        return _ARTIFACTS["macos"]

    raise NotImplementedError(f"Not implemented for this platform {platform}")


class CustomMetadataHook(MetadataHookInterface):
    def update(self, metadata: dict[str, Any]) -> None:
        metadata["entry-points"] = {"vapoursynth": {_PLUGIN_NAMESPACE: get_artifact_name()}}


class CustomBuildHook(BuildHookInterface[WheelBuilderConfig]):
    def initialize(self, version: str, build_data: dict[str, Any]) -> None:
        artifact_name = get_artifact_name()

        build_data["extra_metadata"][f"build/{artifact_name}"] = artifact_name
        build_data["infer_tag"] = True
        build_data["pure_python"] = False
