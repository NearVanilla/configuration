#!/usr/bin/env python3
import subprocess
import sys
from dataclasses import dataclass
from typing import Iterable
from pathlib import Path
import click


@dataclass(frozen=True)
class Region:
    x: int
    z: int

    @property
    def name(self) -> str:
        return f"r.{self.x}.{self.z}.mca"


@dataclass(frozen=True)
class Square:
    x1: int
    z1: int
    x2: int
    z2: int

    @property
    def mca_exclude(self) -> str:
        """The MCA Selector exclusion query"""
        return f"!(xPos >= {block_to_chunk_coord(self.smaller_x)} AND xPos <= {block_to_chunk_coord(self.bigger_x)} AND zPos >= {block_to_chunk_coord(self.smaller_z)} AND zPos <= {block_to_chunk_coord(self.bigger_z)})"

    @property
    def smaller_x(self) -> int:
        return min(self.x1, self.x2)

    @property
    def bigger_x(self) -> int:
        return max(self.x1, self.x2)

    @property
    def smaller_z(self) -> int:
        return min(self.z1, self.z2)

    @property
    def bigger_z(self) -> int:
        return max(self.z1, self.z2)

    def get_spanned_regions(self) -> Iterable[Region]:
        """Get all regions which contain any block within this area"""
        for x in range(
            block_to_region_coord(self.smaller_x),
            block_to_region_coord(self.bigger_x) + 1,
        ):
            for z in range(
                block_to_region_coord(self.smaller_z),
                block_to_region_coord(self.bigger_z) + 1,
            ):
                yield Region(x=x, z=z)


def run_mcaselector(
    dimension_dir: str, query: str, mcaselector_jar: str = "mcaselector.jar"
):
    if not Path(mcaselector_jar).exists():
        raise ValueError(
            f"The mcaselector jar file does not exist! Tried '{mcaselector_jar}'"
        )
    subprocess.run(
        args=[
            "java",
            "-jar",
            mcaselector_jar,
            "--mode",
            "delete",
            "--world",
            dimension_dir,
            "--query",
            query,
        ],
        check=True,
    )


def block_to_chunk_coord(coord: int) -> int:
    return coord >> 5


def block_to_region_coord(coord: int) -> int:
    return coord >> 10


EXCLUSIONS = [
    Square(x1=1111, z1=1111, x2=-1111, z2=-1111),  # Spawn island
]


def get_mca_regions(dimension_dir: str) -> Iterable[Region]:
    region_dir = Path(dimension_dir) / "region"
    if not region_dir.exists():
        raise ValueError(f"The region dir '{region_dir}' does not exist!")
    for region_file in region_dir.glob("r.*.*.mca"):
        split = region_file.name.split(".")
        assert (
            len(split) == 4
        ), f"Expected split of region '{region_file.name}' to produce 4 parts, got '{split}' instead"
        r, x, z, mca = split
        assert (
            r == "r" and mca == "mca"
        ), f"First or last part of the split for '{region_file.name}' are invalid ({r} and {mca} respectively)"
        yield Region(x=int(x), z=int(z))


def delete_mca_regions(dimension_dir: str, regions_to_delete: Iterable[Region]):
    subdirs = ("region", "poi", "entities")
    subdir_paths = tuple(Path(dimension_dir) / subdir for subdir in subdirs)
    if not all(subdir.exists() for subdir in subdir_paths):
        raise ValueError(
            f"One of required subdirs for dimension '{dimension_dir}' does not exist!"
        )
    to_delete = []
    for region in regions_to_delete:
        for subdir in subdir_paths:
            file = subdir / region.name
            if file.exists():
                to_delete.append(file)
            elif subdir.name == "region":
                raise ValueError(
                    f"The region scheduled for deletion does not exist: {file}"
                )
    for file in to_delete:
        file.unlink()


@click.group()
def cli():
    pass


@cli.command()
@click.option("--dimension-dir", help="Directory of the dimension to reset")
@click.option(
    "--mcaselector-jar", default="mcaselector.jar", help="The path to mcaselector jar"
)
def reset_end(dimension_dir: str, mcaselector_jar: str):
    regions = set(get_mca_regions(dimension_dir))
    for exclusion in EXCLUSIONS:
        regions = regions.difference(exclusion.get_spanned_regions())

    print(f"Will delete {len(regions)} regions")

    delete_mca_regions(dimension_dir, regions)

    print("Prunning further with mcaselector...")

    run_mcaselector(
        dimension_dir=dimension_dir,
        query=" AND ".join(exclusion.mca_exclude for exclusion in EXCLUSIONS),
        mcaselector_jar=mcaselector_jar,
    )


if __name__ == "__main__":
    cli()
