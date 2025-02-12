#!/usr/bin/python3
################################################################################
"""
Diashow; showing images like a diashow :-)

(c) 2025, Bernd Roffmann
"""
################################################################################
# flake8: noqa
# pylint: disable=line-too-long
# pylint: disable=missing-function-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=invalid-name

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, final
from enum import Enum

import os
import pygame
import pygame_menu
import exiftool

#-------------------------------------------------------------------------------

DIASHOW_FOLDER = "/media/sf_Exchange/Diashow/"

FILENAME_TAG = "SourceFile"
RATING_TAG = "XMP:Rating"

#-------------------------------------------------------------------------------

@dataclass
@final
class DiashowNode:
    nodename: str
    child_nodes: List[DiashowNode]
    folder: str
    images: List[DiashowImage]

    def __lt__(self, other: DiashowNode) -> bool:
        return self.nodename < other.nodename

@dataclass
@final
class DiashowImage:
    filename: str
    rating: int

    def __lt__(self, other: DiashowNode) -> bool:
        return self.filename < other.filename

def print_diashow_nodes(node: DiashowNode, level: int = 0) -> None:
    tabs = "\t" * level
    print(f"{tabs}Node: {node.nodename} ({node.folder})")
    for image in node.images:
        print(f"{tabs}      Image: {image}")
    for child in node.child_nodes:
        print_diashow_nodes(child, level + 1)

@final
class Diashow:
    def __init__(self, main_folder: str):
        self.__main_folder = main_folder

    def __read_sorted_nodes(self, node: DiashowNode) -> None:
        for child_nodename in os.listdir(node.folder):
            child_folder = os.path.join(node.folder, child_nodename)
            if os.path.isdir(child_folder):
                child_node = DiashowNode(
                    nodename=child_nodename,
                    child_nodes=[],
                    folder=child_folder,
                    images=[],
                )
                node.child_nodes.append(child_node)
                self.__read_sorted_nodes(child_node)
        node.child_nodes.sort()

    def __read_sorted_images(self, node: DiashowNode) -> None:
        # read all files from folder
        filename_list: List[str] = []
        for filename in os.listdir(node.folder):
            filename = os.path.join(node.folder, filename)
            if os.path.isfile(filename) and filename.upper().endswith(".JPG"):
                filename_list.append(filename)

        # create image objects
        if filename_list:
            with exiftool.ExifToolHelper() as et:
                for tag_dict in et.get_tags(filename_list, RATING_TAG):
                    filename = tag_dict[FILENAME_TAG]
                    if RATING_TAG in tag_dict:
                        rating = int(tag_dict[RATING_TAG])
                    else:
                        rating = 0
                    node.images.append(
                        DiashowImage(
                            filename=filename,
                            rating=rating,
                        )
                    )
            node.images.sort()

        # create child objects
        for child in node.child_nodes:
            self.__read_sorted_images(child)

    def read(self) -> DiashowNode:
        main_node = DiashowNode(
            nodename="main",
            child_nodes=[],
            folder=os.path.join(self.__main_folder, ""),
            images=[],
        )
        self.__read_sorted_nodes(main_node)
        self.__read_sorted_images(main_node)
        return main_node

#-------------------------------------------------------------------------------

@dataclass
@final
class TimeDefinition:
    seconds: float
    text: str

@final
class TimeValue(Enum):
    T_00_250_SECS = TimeDefinition(0.250, "250 ms")
    T_00_500_SECS = TimeDefinition(0.500, "500 ms")
    T_00_750_SECS = TimeDefinition(0.750, "750 ms")
    T_01_000_SECS = TimeDefinition(1.000, "1,0 s")
    T_01_500_SECS = TimeDefinition(1.500, "1,5 s")
    T_02_000_SECS = TimeDefinition(2.000, "2,0 s")
    T_02_500_SECS = TimeDefinition(2.500, "2,5 s")
    T_03_000_SECS = TimeDefinition(3.000, "3 s")
    T_04_000_SECS = TimeDefinition(4.000, "4 s")
    T_05_000_SECS = TimeDefinition(5.000, "5 s")
    T_06_000_SECS = TimeDefinition(6.000, "6 s")
    T_07_000_SECS = TimeDefinition(7.000, "7 s")
    T_08_000_SECS = TimeDefinition(8.000, "8 s")
    T_10_000_SECS = TimeDefinition(10.00, "10 s")
    T_15_000_SECS = TimeDefinition(15.00, "15 s")
    T_20_000_SECS = TimeDefinition(20.00, "20 s")
    T_30_000_SECS = TimeDefinition(30.00, "30 s")

@dataclass
@final
class RatingWeighting:
    star_5: int
    star_4: int
    star_3: int
    star_2: int
    star_1: int
    star_0: int

@dataclass
@final
class DiashowConfig:
    min_time_per_image: TimeValue
    max_time_per_image: TimeValue
    blending_time: Optional[TimeValue]
    weighting: RatingWeighting
    show_duration_in_minutes: int

@dataclass
@final
class Config:
    default_diashow_config_s: DiashowConfig
    default_diashow_config_m: DiashowConfig
    default_diashow_config_l: DiashowConfig
    default_diashow_config_x: DiashowConfig
    max_image_count_for_s: int
    max_image_count_for_m: int
    max_image_count_for_l: int

def create_default_weighting() -> RatingWeighting:
    return RatingWeighting(
        star_5 = 125,
        star_4 = 125,
        star_3 = 100,
        star_2 = 75,
        star_1 = 50,
        star_0 = 100,
    )

def create_default_config() -> Config:
    return Config(
        default_diashow_config_s = DiashowConfig(
            min_time_per_image = TimeValue.T_03_000_SECS,
            max_time_per_image = TimeValue.T_10_000_SECS,
            blending_time = None,
            weighting = create_default_weighting(),
            show_duration_in_minutes = 3,
        ),
        default_diashow_config_m = DiashowConfig(
            min_time_per_image = TimeValue.T_03_000_SECS,
            max_time_per_image = TimeValue.T_10_000_SECS,
            blending_time = None,
            weighting = create_default_weighting(),
            show_duration_in_minutes = 7,
        ),
        default_diashow_config_l = DiashowConfig(
            min_time_per_image = TimeValue.T_02_000_SECS,
            max_time_per_image = TimeValue.T_08_000_SECS,
            blending_time = None,
            weighting = create_default_weighting(),
            show_duration_in_minutes = 12,
        ),
        default_diashow_config_x = DiashowConfig(
            min_time_per_image = TimeValue.T_02_000_SECS,
            max_time_per_image = TimeValue.T_08_000_SECS,
            blending_time = None,
            weighting = create_default_weighting(),
            show_duration_in_minutes = 18,
        ),
        max_image_count_for_s = 30 * 1,
        max_image_count_for_m = 30 * 3,
        max_image_count_for_l = 30 * 9,
    )

@dataclass
@final
class DiashowTiming:
    star_5_image_duration_in_seconds: float
    star_4_image_duration_in_seconds: float
    star_3_image_duration_in_seconds: float
    star_2_image_duration_in_seconds: float
    star_1_image_duration_in_seconds: float
    star_0_image_duration_in_seconds: float
    blending_time_in_seconds: float
    show_duration_in_minutes: float

@final
class DiashowCalculator:
    def __init__(self, images: List[DiashowImage]):
        self.__images = images
        assert len(self.__images) > 0
        self.__5_star_cnt = 0
        self.__4_star_cnt = 0
        self.__3_star_cnt = 0
        self.__2_star_cnt = 0
        self.__1_star_cnt = 0
        self.__0_star_cnt = 0
        for image in self.__images:
            if image.rating == 2:
                self.__2_star_cnt += 1
            elif image.rating == 3:
                self.__3_star_cnt += 1
            elif image.rating == 4:
                self.__4_star_cnt += 1
            elif image.rating == 5:
                self.__5_star_cnt += 1
            elif image.rating == 1:
                self.__1_star_cnt += 1
            else:
                self.__0_star_cnt += 1

    @staticmethod
    def __calc_image_duration(diashow_config: DiashowConfig, show_duration_in_seconds_per_weight: float, weighting: int) -> float:
        result = show_duration_in_seconds_per_weight * float(weighting)
        min_duration = diashow_config.min_time_per_image.value.seconds
        max_duration = diashow_config.max_time_per_image.value.seconds
        if result < min_duration:
            return min_duration
        elif result > max_duration:
            return max_duration
        else:
            return result

    def calc(self, diashow_config: DiashowConfig) -> DiashowTiming:
        weighting_sum = float(
            self.__5_star_cnt * diashow_config.weighting.star_5 +
            self.__4_star_cnt * diashow_config.weighting.star_4 +
            self.__3_star_cnt * diashow_config.weighting.star_3 +
            self.__2_star_cnt * diashow_config.weighting.star_2 +
            self.__1_star_cnt * diashow_config.weighting.star_1 +
            self.__0_star_cnt * diashow_config.weighting.star_0
        )
        show_duration_in_seconds = float(diashow_config.show_duration_in_minutes) * 60.0
        show_duration_in_seconds_per_weight = show_duration_in_seconds / weighting_sum
        if diashow_config.blending_time is None:
            blending_time_in_seconds = 0.0
        else:
            blending_time_in_seconds = diashow_config.blending_time.value.seconds
        timing = DiashowTiming(
            star_5_image_duration_in_seconds=self.__calc_image_duration(diashow_config, show_duration_in_seconds_per_weight, diashow_config.weighting.star_5),
            star_4_image_duration_in_seconds=self.__calc_image_duration(diashow_config, show_duration_in_seconds_per_weight, diashow_config.weighting.star_4),
            star_3_image_duration_in_seconds=self.__calc_image_duration(diashow_config, show_duration_in_seconds_per_weight, diashow_config.weighting.star_3),
            star_2_image_duration_in_seconds=self.__calc_image_duration(diashow_config, show_duration_in_seconds_per_weight, diashow_config.weighting.star_2),
            star_1_image_duration_in_seconds=self.__calc_image_duration(diashow_config, show_duration_in_seconds_per_weight, diashow_config.weighting.star_1),
            star_0_image_duration_in_seconds=self.__calc_image_duration(diashow_config, show_duration_in_seconds_per_weight, diashow_config.weighting.star_0),
            blending_time_in_seconds=blending_time_in_seconds,
            show_duration_in_minutes=0.0,
        )
        actual_duration_in_seconds = \
            float(self.__5_star_cnt) * timing.star_5_image_duration_in_seconds + \
            float(self.__4_star_cnt) * timing.star_4_image_duration_in_seconds + \
            float(self.__3_star_cnt) * timing.star_3_image_duration_in_seconds + \
            float(self.__2_star_cnt) * timing.star_2_image_duration_in_seconds + \
            float(self.__1_star_cnt) * timing.star_1_image_duration_in_seconds + \
            float(self.__0_star_cnt) * timing.star_0_image_duration_in_seconds
        timing.show_duration_in_minutes = actual_duration_in_seconds / 60.0
        return timing

#-------------------------------------------------------------------------------

@final
class DiashowXXX:
    def __init__(self, surface: pygame.Surface):
        self.__surface = surface

    def __create_menu(self, label: str, theme: pygame_menu.Theme) -> pygame_menu.Menu:
        return pygame_menu.Menu(
            title=label,
            height=self.__surface.get_height(),
            width=self.__surface.get_width(),
            theme=theme,
        )

    def main(self):
        select_diashow_menu = self.__create_menu("Diashow auswählen", pygame_menu.themes.THEME_DARK)
        select_diashow_menu.add.button("Zurück", pygame_menu.events.BACK)


        menu = self.__create_menu("Diashow", pygame_menu.themes.THEME_BLUE)
        menu.add.button("Diashow auswählen", select_diashow_menu)
        menu.add.button("Exit", pygame_menu.events.EXIT)
        menu.mainloop(self.__surface)

#-------------------------------------------------------------------------------

def main():
    assert os.path.exists(DIASHOW_FOLDER)
    nodes = Diashow(DIASHOW_FOLDER).read()
    print_diashow_nodes(nodes)

    config = create_default_config()

    # TEST
    test_images = nodes.child_nodes[0].child_nodes[0].images
    calculator = DiashowCalculator(test_images)
    timing = calculator.calc(config.default_diashow_config_s)
    print()
    print(timing)


    #pygame.init()
    #surface = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    #diashow = Diashow(surface)
    #diashow.main()

#-------------------------------------------------------------------------------

if __name__ == "__main__":
    main()
