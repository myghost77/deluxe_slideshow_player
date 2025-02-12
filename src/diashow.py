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
# pylint: disable=unnecessary-lambda

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple, Any, Optional, final
from enum import Enum
from abc import ABC, abstractmethod

import os
import time
import pygame
import pygame_menu
import exiftool

#-------------------------------------------------------------------------------

def get_current_time_since_epoch_in_seconds() -> float:
    return time.time()

#-------------------------------------------------------------------------------

DIASHOW_FOLDER = "/media/sf_Exchange/Diashow/"

FILENAME_TAG = "SourceFile"
RATING_TAG = "XMP:Rating"

SCRIPT_PATH, SCRIPT_NAME = os.path.split(__file__)

BACKGROUND_IMAGE = pygame_menu.BaseImage(
    image_path=os.path.join(SCRIPT_PATH, "background.jpg"),
)

DEFAULT_VERTICAL_MARGIN = 35

FPS = 25

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

    def __lt__(self, other: DiashowImage) -> bool:
        return self.filename < other.filename

def print_diashow_nodes(node: DiashowNode, level: int = 0) -> None:
    tabs = "\t" * level
    print(f"{tabs}Node: {node.nodename} ({node.folder})")
    for image in node.images:
        print(f"{tabs}      Image: {image}")
    for child in node.child_nodes:
        print_diashow_nodes(child, level + 1)

@final
class DiashowReader:
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
            nodename="",
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

TIME_VALUE_SELECTOR_LIST: List[Tuple[str, TimeValue]] = [
    (item.value.text, item)
    for item in TimeValue
]

#-------------------------------------------------------------------------------

@dataclass
@final
class RatingWeighting:
    star_5: int
    star_4: int
    star_3: int
    star_2: int
    star_1: int
    star_0: int

    def copy(self) -> RatingWeighting:
        return RatingWeighting(
            star_5=self.star_5,
            star_4=self.star_4,
            star_3=self.star_3,
            star_2=self.star_2,
            star_1=self.star_1,
            star_0=self.star_0,
        )

@dataclass
@final
class DiashowConfig:
    min_time_per_image: TimeValue
    max_time_per_image: TimeValue
    blending_time: Optional[TimeValue]
    weighting: RatingWeighting
    show_duration_in_minutes: float

    def copy(self) -> DiashowConfig:
        return DiashowConfig(
            min_time_per_image=self.min_time_per_image,
            max_time_per_image=self.max_time_per_image,
            blending_time=self.blending_time,
            weighting=self.weighting.copy(),
            show_duration_in_minutes=self.show_duration_in_minutes,
        )

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
            show_duration_in_minutes = 2.5,
        ),
        default_diashow_config_m = DiashowConfig(
            min_time_per_image = TimeValue.T_03_000_SECS,
            max_time_per_image = TimeValue.T_10_000_SECS,
            blending_time = None,
            weighting = create_default_weighting(),
            show_duration_in_minutes = 7.5,
        ),
        default_diashow_config_l = DiashowConfig(
            min_time_per_image = TimeValue.T_02_000_SECS,
            max_time_per_image = TimeValue.T_08_000_SECS,
            blending_time = None,
            weighting = create_default_weighting(),
            show_duration_in_minutes = 15.0,
        ),
        default_diashow_config_x = DiashowConfig(
            min_time_per_image = TimeValue.T_02_000_SECS,
            max_time_per_image = TimeValue.T_08_000_SECS,
            blending_time = None,
            weighting = create_default_weighting(),
            show_duration_in_minutes = 20.0,
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
        show_duration_in_seconds = diashow_config.show_duration_in_minutes * 60.0
        show_duration_in_seconds_per_weight = show_duration_in_seconds / weighting_sum
        timing = DiashowTiming(
            star_5_image_duration_in_seconds=self.__calc_image_duration(diashow_config, show_duration_in_seconds_per_weight, diashow_config.weighting.star_5),
            star_4_image_duration_in_seconds=self.__calc_image_duration(diashow_config, show_duration_in_seconds_per_weight, diashow_config.weighting.star_4),
            star_3_image_duration_in_seconds=self.__calc_image_duration(diashow_config, show_duration_in_seconds_per_weight, diashow_config.weighting.star_3),
            star_2_image_duration_in_seconds=self.__calc_image_duration(diashow_config, show_duration_in_seconds_per_weight, diashow_config.weighting.star_2),
            star_1_image_duration_in_seconds=self.__calc_image_duration(diashow_config, show_duration_in_seconds_per_weight, diashow_config.weighting.star_1),
            star_0_image_duration_in_seconds=self.__calc_image_duration(diashow_config, show_duration_in_seconds_per_weight, diashow_config.weighting.star_0),
            blending_time_in_seconds=0.0,
            show_duration_in_minutes=0.0,
        )
        if diashow_config.blending_time is not None:
            min_image_duration = min(
                timing.star_5_image_duration_in_seconds,
                timing.star_4_image_duration_in_seconds,
                timing.star_3_image_duration_in_seconds,
                timing.star_2_image_duration_in_seconds,
                timing.star_1_image_duration_in_seconds,
                timing.star_0_image_duration_in_seconds,
            )
            max_blending_time_in_seconds = min_image_duration / 3.0
            act_blending_time_in_seconds = diashow_config.blending_time.value.seconds
            if act_blending_time_in_seconds > max_blending_time_in_seconds:
                timing.blending_time_in_seconds = max_blending_time_in_seconds
            else:
                timing.blending_time_in_seconds = act_blending_time_in_seconds
        actual_duration_in_seconds = \
            float(self.__5_star_cnt) * timing.star_5_image_duration_in_seconds + \
            float(self.__4_star_cnt) * timing.star_4_image_duration_in_seconds + \
            float(self.__3_star_cnt) * timing.star_3_image_duration_in_seconds + \
            float(self.__2_star_cnt) * timing.star_2_image_duration_in_seconds + \
            float(self.__1_star_cnt) * timing.star_1_image_duration_in_seconds + \
            float(self.__0_star_cnt) * timing.star_0_image_duration_in_seconds + \
            timing.blending_time_in_seconds  # there is one more blending
        timing.show_duration_in_minutes = actual_duration_in_seconds / 60.0
        return timing

#-------------------------------------------------------------------------------

NO_BLENDING_TEXT = "ohne Überblendung"

BLENDING_TIME_VALUE_SELECTOR_LIST: List[Tuple[str, Optional[TimeValue]]] = []
BLENDING_TIME_VALUE_SELECTOR_LIST.append((NO_BLENDING_TEXT, None))
for item in TimeValue:
    if item.value.seconds <= 3.0:
        BLENDING_TIME_VALUE_SELECTOR_LIST.append((item.value.text, item))

def get_blending_time_text(blending_time: Optional[TimeValue]) -> str:
    if blending_time is None:
        return NO_BLENDING_TEXT
    else:
        return blending_time.value.text

#-------------------------------------------------------------------------------

class MenuFactory(ABC):
    @abstractmethod
    def create_menu(self, menu_creator: MenuCreator, menu_title: str, back_text: str) -> pygame_menu.Menu:
        pass

class MenuStarter(ABC):
    @abstractmethod
    def start(self, menu_creator: MenuCreator) -> None:
        pass

#-------------------------------------------------------------------------------

@final
class MenuCreator:
    def __init__(self, surface: pygame.Surface):
        self.__surface = surface
        self.__theme_1 = pygame_menu.themes.THEME_BLUE.copy()
        self.__theme_1.background_color = BACKGROUND_IMAGE
        self.__theme_1.selection_color = (212, 212, 212)
        self.__theme_1.widget_font_shadow = True
        self.__theme_2 = self.__theme_1.copy()
        self.__theme_2.background_color = (0, 0, 128)
        self.__theme_2.set_background_color_opacity(0.5)

    def get_surface(self) -> pygame.Surface:
        return self.__surface

    def create_menu(self, menu_title: str, height: Optional[int] = None, width: Optional[int] = None, theme_nr = 1) -> pygame_menu.Menu:
        if height is None:
            height = self.__surface.get_height()
        if width is None:
            width = self.__surface.get_width()
        if theme_nr == 1:
            theme = self.__theme_1
        else:
            theme = self.__theme_2
        return pygame_menu.Menu(
            title=menu_title,
            height=height,
            width=width,
            theme=theme,
        )

@final
class DiashowOptionsMenuFactory(MenuFactory):
    def __init__(self, diashow_config: DiashowConfig):
        self.__diashow_config = diashow_config

    def __set_min_time_per_image(self, _: Tuple, value: Any) -> None:
        assert isinstance(value, TimeValue)
        self.__diashow_config.min_time_per_image = value

    def __set_max_time_per_image(self, _: Tuple, value: Any) -> None:
        assert isinstance(value, TimeValue)
        self.__diashow_config.max_time_per_image = value

    def __set_blending_time(self, _: Tuple, value: Any) -> None:
        assert value is None or isinstance(value, TimeValue)
        self.__diashow_config.blending_time = value

    def __set_weighting_star_5(self, value: Any) -> None:
        assert isinstance(value, float)
        self.__diashow_config.weighting.star_5 = round(value)

    def __set_weighting_star_4(self, value: Any) -> None:
        assert isinstance(value, float)
        self.__diashow_config.weighting.star_4 = round(value)

    def __set_weighting_star_3(self, value: Any) -> None:
        assert isinstance(value, float)
        self.__diashow_config.weighting.star_3 = round(value)

    def __set_weighting_star_2(self, value: Any) -> None:
        assert isinstance(value, float)
        self.__diashow_config.weighting.star_2 = round(value)

    def __set_weighting_star_1(self, value: Any) -> None:
        assert isinstance(value, float)
        self.__diashow_config.weighting.star_1 = round(value)

    def __set_weighting_star_0(self, value: Any) -> None:
        assert isinstance(value, float)
        self.__diashow_config.weighting.star_0 = round(value)

    def __set_show_duration_in_minutes(self, value: Any) -> None:
        assert isinstance(value, float)
        self.__diashow_config.show_duration_in_minutes = value

    def create_menu(self, menu_creator: MenuCreator, menu_title: str, back_text: str) -> pygame_menu.Menu:
        menu = menu_creator.create_menu(menu_title)
        menu.add.selector("Minimale Standzeit pro Bild: ", TIME_VALUE_SELECTOR_LIST, onchange=self.__set_min_time_per_image) \
            .set_value(self.__diashow_config.min_time_per_image.value.text)
        menu.add.selector("Maximale Standzeit pro Bild: ", TIME_VALUE_SELECTOR_LIST, onchange=self.__set_max_time_per_image) \
            .set_value(self.__diashow_config.max_time_per_image.value.text)
        menu.add.vertical_margin(DEFAULT_VERTICAL_MARGIN)
        menu.add.selector("Geplante Überblendzeit: ", BLENDING_TIME_VALUE_SELECTOR_LIST, onchange=self.__set_blending_time) \
            .set_value(get_blending_time_text(self.__diashow_config.blending_time))
        menu.add.vertical_margin(DEFAULT_VERTICAL_MARGIN)
        menu.add.range_slider("Standzeitgewichtung für 5*-Bilder: ", float(self.__diashow_config.weighting.star_5), (25.0, 200.0), increment=5.0,
            value_format=lambda x: str(round(x)), onchange=self.__set_weighting_star_5)
        menu.add.range_slider("Standzeitgewichtung für 4*-Bilder: ", float(self.__diashow_config.weighting.star_4), (25.0, 200.0), increment=5.0,
            value_format=lambda x: str(round(x)), onchange=self.__set_weighting_star_4)
        menu.add.range_slider("Standzeitgewichtung für 3*-Bilder: ", float(self.__diashow_config.weighting.star_3), (25.0, 200.0), increment=5.0,
            value_format=lambda x: str(round(x)), onchange=self.__set_weighting_star_3)
        menu.add.range_slider("Standzeitgewichtung für 2*-Bilder: ", float(self.__diashow_config.weighting.star_2), (25.0, 200.0), increment=5.0,
            value_format=lambda x: str(round(x)), onchange=self.__set_weighting_star_2)
        menu.add.range_slider("Standzeitgewichtung für 1*-Bilder: ", float(self.__diashow_config.weighting.star_1), (25.0, 200.0), increment=5.0,
            value_format=lambda x: str(round(x)), onchange=self.__set_weighting_star_1)
        menu.add.range_slider("Standzeitgewichtung für 0*-Bilder: ", float(self.__diashow_config.weighting.star_0), (25.0, 200.0), increment=5.0,
            value_format=lambda x: str(round(x)), onchange=self.__set_weighting_star_0)
        menu.add.vertical_margin(DEFAULT_VERTICAL_MARGIN)
        menu.add.range_slider("Geplante Gesamtzeit: ", self.__diashow_config.show_duration_in_minutes, (1.0, 120.0), increment=0.5,
            value_format=lambda x: f"{round(x, 1)} Minute(n)", onchange=self.__set_show_duration_in_minutes, width=200)
        menu.add.vertical_margin(DEFAULT_VERTICAL_MARGIN)
        menu.add.button(back_text, pygame_menu.events.BACK)
        return menu

@final
class OptionsMenuFactory(MenuFactory):
    def __init__(self, config: Config):
        self.__config = config
        self.__default_diashow_options_menu_s = DiashowOptionsMenuFactory(self.__config.default_diashow_config_s)
        self.__default_diashow_options_menu_m = DiashowOptionsMenuFactory(self.__config.default_diashow_config_m)
        self.__default_diashow_options_menu_l = DiashowOptionsMenuFactory(self.__config.default_diashow_config_l)
        self.__default_diashow_options_menu_x = DiashowOptionsMenuFactory(self.__config.default_diashow_config_x)

    def __set_max_image_count_for_s(self, value: Any) -> None:
        assert isinstance(value, float)
        self.__config.max_image_count_for_s = round(value)

    def __set_max_image_count_for_m(self, value: Any) -> None:
        assert isinstance(value, float)
        self.__config.max_image_count_for_m = round(value)

    def __set_max_image_count_for_l(self, value: Any) -> None:
        assert isinstance(value, float)
        self.__config.max_image_count_for_l = round(value)

    def create_menu(self, menu_creator: MenuCreator, menu_title: str, back_text: str) -> pygame_menu.Menu:
        default_diashow_config_s_text = "(Standard-)Einstellungen für sehr kleine Diashows"
        default_diashow_config_m_text = "(Standard-)Einstellungen für mittelgroße Diashows"
        default_diashow_config_l_text = "(Standard-)Einstellungen für große Diashows"
        default_diashow_config_x_text = "(Standard-)Einstellungen für sehr große Diashows"
        menu = menu_creator.create_menu(menu_title)
        menu.add.range_slider("Maximale Anzahl Bilder für sehr kleine Diashows: ", self.__config.max_image_count_for_s, (10.0, 125.0), increment=5.0,
            value_format=lambda x: str(round(x)), onchange=self.__set_max_image_count_for_s)
        menu.add.range_slider("Maximale Anzahl Bilder für mittelgroße Diashows: ", self.__config.max_image_count_for_m, (75.0, 250.0), increment=5.0,
            value_format=lambda x: str(round(x)), onchange=self.__set_max_image_count_for_m)
        menu.add.range_slider("Maximale Anzahl Bilder für große Diashows: ", self.__config.max_image_count_for_l, (125.0, 500.0), increment=5.0,
            value_format=lambda x: str(round(x)), onchange=self.__set_max_image_count_for_l)
        menu.add.vertical_margin(DEFAULT_VERTICAL_MARGIN)
        menu.add.button(default_diashow_config_s_text, self.__default_diashow_options_menu_s.create_menu(
            menu_creator=menu_creator,
            menu_title=default_diashow_config_s_text,
            back_text=back_text,
        ))
        menu.add.button(default_diashow_config_m_text, self.__default_diashow_options_menu_m.create_menu(
            menu_creator=menu_creator,
            menu_title=default_diashow_config_m_text,
            back_text=back_text,
        ))
        menu.add.button(default_diashow_config_l_text, self.__default_diashow_options_menu_l.create_menu(
            menu_creator=menu_creator,
            menu_title=default_diashow_config_l_text,
            back_text=back_text,
        ))
        menu.add.button(default_diashow_config_x_text, self.__default_diashow_options_menu_x.create_menu(
            menu_creator=menu_creator,
            menu_title=default_diashow_config_x_text,
            back_text=back_text,
        ))
        menu.add.vertical_margin(DEFAULT_VERTICAL_MARGIN)
        menu.add.button(back_text, pygame_menu.events.BACK)
        return menu

@final
class MainMenu(MenuStarter):
    DIASHOW_PLAY_MODE = "SHOW"
    SAVE_CONFIG_MODE = "SAVE"
    EXIT_MODE = "EXIT"

    def __init__(self, menu: pygame_menu.Menu):
        self.__menu = menu
        self.__play_mode: Optional[str] = None
        self.__play_node: Optional[DiashowNode] = None
        self.__hierachy: Optional[List[DiashowNode]] = None

    def play_diashow(self, play_node: DiashowNode, hierachy: List[DiashowNode]):
        self.__menu.disable()
        self.__play_mode = self.DIASHOW_PLAY_MODE
        self.__play_node = play_node
        self.__hierachy = hierachy

    def save_options(self):
        self.__menu.disable()
        self.__play_mode = self.SAVE_CONFIG_MODE
        self.__play_node = None
        self.__hierachy = None

    def exit(self):
        self.__menu.disable()
        self.__play_mode = self.EXIT_MODE
        self.__play_node = None
        self.__hierachy = None

    def get_play_mode(self) -> str:
        assert self.__play_mode is not None
        return self.__play_mode

    def get_play_node(self) -> DiashowNode:
        assert self.__play_node is not None
        return self.__play_node

    def get_hierachy(self) -> List[DiashowNode]:
        assert self.__hierachy is not None
        return self.__hierachy

    def start(self, menu_creator: MenuCreator) -> None:
        self.__play_mode = None
        self.__play_node = None
        self.__hierachy = None
        self.__menu.enable()
        self.__menu.mainloop(menu_creator.get_surface(), fps_limit=FPS)

@final
class DiashowMenuFactory(MenuFactory):
    def __init__(self, main_menu: MainMenu, play_node: DiashowNode, hierachy: List[DiashowNode]):
        self.__main_menu = main_menu
        self.__play_node = play_node
        self.__hierachy = hierachy

    def create_menu(self, menu_creator: MenuCreator, menu_title: str, back_text: str) -> pygame_menu.Menu:
        menu = menu_creator.create_menu(menu_title)
        if len(self.__hierachy) > 0:
            for hierachy_node in self.__hierachy:
                menu.add.label(hierachy_node.nodename)
            menu.add.vertical_margin(DEFAULT_VERTICAL_MARGIN)
        if len(self.__play_node.images) > 0:
            menu.add.button("Zur Diashow", lambda: self.__main_menu.play_diashow(self.__play_node, self.__hierachy))
            menu.add.vertical_margin(DEFAULT_VERTICAL_MARGIN)
        if len(self.__play_node.child_nodes) > 0:
            for child_node in self.__play_node.child_nodes:
                child_diashow_menu_factory = DiashowMenuFactory(
                    main_menu=self.__main_menu,
                    play_node=child_node,
                    hierachy=self.__hierachy + [child_node],
                )
                menu.add.button(child_node.nodename, child_diashow_menu_factory.create_menu(
                    menu_creator=menu_creator,
                    menu_title=menu_title,
                    back_text=back_text,
                ))
            menu.add.vertical_margin(DEFAULT_VERTICAL_MARGIN)
        menu.add.button(back_text, pygame_menu.events.BACK)
        return menu

@final
class MainMenuCreator:
    def __init__(self, main_node: DiashowNode, config: Config):
        self.__main_node = main_node
        self.__options_menu_factory = OptionsMenuFactory(config)

    def create_main(self, menu_creator: MenuCreator) -> MainMenu:
        select_diashow_text = "Diashow auswählen"
        change_options_text = "Optionen anpassen"
        save_options_text = "Optionen speichern"
        back_text = "Zurück"
        menu = menu_creator.create_menu("Diashow")
        main_menu = MainMenu(menu)
        menu.add.button(select_diashow_text, DiashowMenuFactory(main_menu=main_menu, play_node=self.__main_node, hierachy=[]).create_menu(
            menu_creator=menu_creator,
            menu_title=select_diashow_text,
            back_text=back_text,
        ))
        menu.add.button(change_options_text, self.__options_menu_factory.create_menu(
            menu_creator=menu_creator,
            menu_title=change_options_text,
            back_text=back_text,
        ))
        # TODO: menu.add.button(save_options_text, main_menu.save_options)
        menu.add.vertical_margin(DEFAULT_VERTICAL_MARGIN)
        menu.add.button("Verlassen", main_menu.exit)
        return main_menu

@final
class DiashowStartMenu(MenuFactory, MenuStarter):
    @staticmethod
    def create_diashow_config(config: Config, play_node: DiashowNode) -> DiashowConfig:
        image_count = len(play_node.images)
        if image_count <= config.max_image_count_for_s:
            return config.default_diashow_config_s.copy()
        elif image_count <= config.max_image_count_for_m:
            return config.default_diashow_config_m.copy()
        elif image_count <= config.max_image_count_for_l:
            return config.default_diashow_config_l.copy()
        else:
            return config.default_diashow_config_x.copy()

    def __init__(self, config: Config, play_node: DiashowNode, hierachy: List[DiashowNode]):
        self.__diashow_config = self.create_diashow_config(config, play_node)
        self.__play_node = play_node
        self.__hierachy = hierachy
        self.__menu: Optional[pygame_menu.Menu] = None
        self.__star_5_image_duration_in_seconds_label: Any = None
        self.__star_4_image_duration_in_seconds_label: Any = None
        self.__star_3_image_duration_in_seconds_label: Any = None
        self.__star_2_image_duration_in_seconds_label: Any = None
        self.__star_1_image_duration_in_seconds_label: Any = None
        self.__star_0_image_duration_in_seconds_label: Any = None
        self.__blending_time_in_seconds_label: Any = None
        self.__show_duration_in_minutes_label: Any = None
        self.__calculator = DiashowCalculator(self.__play_node.images)
        self.__timing: Optional[DiashowTiming] = None
        self.__canceled = False

    def get_diashow_config(self) -> DiashowConfig:
        return self.__diashow_config

    def get_play_node(self) -> DiashowNode:
        return self.__play_node

    def get_timing(self) -> DiashowTiming:
        assert self.__timing is not None
        return self.__timing

    def is_canceled(self) -> bool:
        return self.__canceled

    def update_timing(self) -> None:
        timing = self.__calculator.calc(self.__diashow_config)
        if isinstance(self.__star_5_image_duration_in_seconds_label, pygame_menu.widgets.Label):
            self.__star_5_image_duration_in_seconds_label.set_title(f"Standzeit für 5*-Bilder: {round(timing.star_5_image_duration_in_seconds, 1)} Sekunde(n)")
        if isinstance(self.__star_4_image_duration_in_seconds_label, pygame_menu.widgets.Label):
            self.__star_4_image_duration_in_seconds_label.set_title(f"Standzeit für 4*-Bilder: {round(timing.star_4_image_duration_in_seconds, 1)} Sekunde(n)")
        if isinstance(self.__star_3_image_duration_in_seconds_label, pygame_menu.widgets.Label):
            self.__star_3_image_duration_in_seconds_label.set_title(f"Standzeit für 3*-Bilder: {round(timing.star_3_image_duration_in_seconds, 1)} Sekunde(n)")
        if isinstance(self.__star_2_image_duration_in_seconds_label, pygame_menu.widgets.Label):
            self.__star_2_image_duration_in_seconds_label.set_title(f"Standzeit für 2*-Bilder: {round(timing.star_2_image_duration_in_seconds, 1)} Sekunde(n)")
        if isinstance(self.__star_1_image_duration_in_seconds_label, pygame_menu.widgets.Label):
            self.__star_1_image_duration_in_seconds_label.set_title(f"Standzeit für 1*-Bilder: {round(timing.star_1_image_duration_in_seconds, 1)} Sekunde(n)")
        if isinstance(self.__star_0_image_duration_in_seconds_label, pygame_menu.widgets.Label):
            self.__star_0_image_duration_in_seconds_label.set_title(f"Standzeit für 0*-Bilder: {round(timing.star_0_image_duration_in_seconds, 1)} Sekunde(n)")
        if isinstance(self.__blending_time_in_seconds_label, pygame_menu.widgets.Label):
            self.__blending_time_in_seconds_label.set_title(f"Überblendzeit: {round(timing.blending_time_in_seconds, 2)} Sekunde(n)")
        if isinstance(self.__show_duration_in_minutes_label, pygame_menu.widgets.Label):
            self.__show_duration_in_minutes_label.set_title(f"Gesamtzeit: {round(timing.show_duration_in_minutes, 2)} Minute(n)")
        self.__timing = timing

    def play_diashow(self):
        self.__canceled = False
        self.__menu.disable()

    def cancel(self):
        self.__canceled = True
        self.__menu.disable()

    def create_menu(self, menu_creator: MenuCreator, menu_title: str, back_text: str) -> pygame_menu.Menu:
        play_diashow_text = "Diashow starten"
        adjust_options_text = "Einstellungen anpassen"
        menu = menu_creator.create_menu(play_diashow_text)
        for hierachy_node in self.__hierachy:
            menu.add.label(hierachy_node.nodename)
        menu.add.vertical_margin(DEFAULT_VERTICAL_MARGIN)
        self.__star_5_image_duration_in_seconds_label = menu.add.label("")
        self.__star_4_image_duration_in_seconds_label = menu.add.label("")
        self.__star_3_image_duration_in_seconds_label = menu.add.label("")
        self.__star_2_image_duration_in_seconds_label = menu.add.label("")
        self.__star_1_image_duration_in_seconds_label = menu.add.label("")
        self.__star_0_image_duration_in_seconds_label = menu.add.label("")
        self.__blending_time_in_seconds_label = menu.add.label("")
        menu.add.vertical_margin(DEFAULT_VERTICAL_MARGIN)
        self.__show_duration_in_minutes_label = menu.add.label("")
        menu.add.vertical_margin(DEFAULT_VERTICAL_MARGIN)
        menu.add.button(play_diashow_text, self.play_diashow)
        menu.add.button(adjust_options_text, DiashowOptionsMenuFactory(self.__diashow_config).create_menu(
            menu_creator=menu_creator,
            menu_title=adjust_options_text,
            back_text="Übernehmen",
        ))
        menu.add.button("Abbrechen", self.cancel)
        menu.set_onupdate(self.update_timing)
        return menu

    def start(self, menu_creator: MenuCreator) -> None:
        try:
            self.__canceled = False
            self.__menu = self.create_menu(
                menu_creator=menu_creator,
                menu_title="Diashow starten",
                back_text="Abbrechen",
            )
            self.__menu.mainloop(menu_creator.get_surface(), fps_limit=FPS)
        finally:
            self.__menu = None

#-------------------------------------------------------------------------------

def blit_image_helper(surface: pygame.Surface, image: pygame.Surface)-> None:
    y_pos = (surface.get_height() - image.get_height()) // 2
    x_pos = (surface.get_width() - image.get_width()) // 2
    surface.blit(image, (x_pos, y_pos))

#-------------------------------------------------------------------------------

class DiashowSegment(ABC):
    @abstractmethod
    def get_lifetime_in_seconds(self) -> float:
        pass

    @abstractmethod
    def start(self) -> None:
        pass

    @abstractmethod
    def update(self, surface: pygame.Surface, time_in_seconds: float) -> None:
        pass

@final
class ImageLoader:
    def __init__(self, surface: pygame.Surface, images: List[DiashowImage]):
        self.__surface = surface
        self.__images = images
        self.__image0: Optional[pygame.Surface] = None
        self.__image0_index: Optional[int] = None
        self.__image1: Optional[pygame.Surface] = None
        self.__image1_index: Optional[int] = None

    def __scale_image(self, image: pygame.Surface) -> pygame.Surface:
        if image.get_height() == self.__surface.get_height() and image.get_width() <= self.__surface.get_width():
            return image  # no re-scale
        elif image.get_width() == self.__surface.get_width() and image.get_height() <= self.__surface.get_height():
            return image  # no re-scale
        else:
            surface_height_f = float(self.__surface.get_height())
            surface_width_f = float(self.__surface.get_width())
            image_height_f = float(image.get_height())
            image_width_f = float(image.get_width())
            surface_ratio = surface_width_f / surface_height_f
            image_ration = image_width_f / image_height_f
            if image_ration <= surface_ratio:
                new_image_height = self.__surface.get_height()
                new_image_width = round(surface_height_f / image_height_f * image_width_f)
            else:
                new_image_height = round(surface_width_f / image_width_f * image_height_f)
                new_image_width = self.__surface.get_width()
            return pygame.transform.scale(image, (new_image_width, new_image_height))

    def __check_negative_index(self, index: int) -> int:
        if index < 0:
            index = len(self.__images) + index
        assert index >= 0
        return index

    def load_image(self, index: int) -> None:
        index = self.__check_negative_index(index)

        # check, if it is already loaded
        if index == self.__image0_index or index == self.__image1_index:
            return

        # read image
        if index < len(self.__images):
            image: Optional[pygame.Surface] = self.__scale_image(
                pygame.image.load(self.__images[index].filename).convert_alpha(),
            )
        else:
            image = None

        # set image
        if index % 2 == 0:
            self.__image0_index = index
            self.__image0 = image
        else:
            self.__image1_index = index
            self.__image1 = image

    def get_image(self, index: int) -> Optional[pygame.Surface]:
        index = self.__check_negative_index(index)

        # get image
        if index % 2 == 0:
            return self.__image0
        else:
            return self.__image1

@final
class StartDiashowSegment(DiashowSegment):
    def __init__(self, timing: DiashowTiming, loader: ImageLoader):
        self.__timing = timing
        self.__loader = loader

    def get_lifetime_in_seconds(self) -> float:
        return self.__timing.blending_time_in_seconds

    def start(self) -> None:
        self.__loader.load_image(0)

    def update(self, surface: pygame.Surface, time_in_seconds: float) -> None:
        surface.fill((0, 0, 0))
        if self.__timing.blending_time_in_seconds > 0.0:
            fade_factor = time_in_seconds / self.__timing.blending_time_in_seconds
        else:
            fade_factor = 1.0
        image = self.__loader.get_image(0)
        assert image is not None
        if fade_factor >= 1.0:
            image.set_alpha(255)
        else:
            image.set_alpha(round(255.0 * fade_factor))
        blit_image_helper(surface, image)

@final
class EndDiashowSegment(DiashowSegment):
    def __init__(self, timing: DiashowTiming, loader: ImageLoader):
        self.__timing = timing
        self.__loader = loader

    def get_lifetime_in_seconds(self) -> float:
        return self.__timing.blending_time_in_seconds

    def start(self) -> None:
        self.__loader.load_image(-1)

    def update(self, surface: pygame.Surface, time_in_seconds: float) -> None:
        surface.fill((0, 0, 0))
        if self.__timing.blending_time_in_seconds > 0.0:
            fade_factor = 1.0 - time_in_seconds / self.__timing.blending_time_in_seconds
        else:
            fade_factor = 0.0
        if fade_factor > 0.0:
            image = self.__loader.get_image(-1)
            assert image is not None
            image.set_alpha(round(255.0 * fade_factor))
            blit_image_helper(surface, image)

@final
class CrossFadeDiashowSegment(DiashowSegment):
    def __init__(self, timing: DiashowTiming, loader: ImageLoader, prev_index: int, next_index: int):
        self.__timing = timing
        self.__loader = loader
        self.__prev_index = prev_index
        self.__next_index = next_index

    def get_lifetime_in_seconds(self) -> float:
        return self.__timing.blending_time_in_seconds

    def start(self) -> None:
        self.__loader.load_image(self.__prev_index)
        self.__loader.load_image(self.__next_index)

    def update(self, surface: pygame.Surface, time_in_seconds: float) -> None:
        surface.fill((0, 0, 0))
        if self.__timing.blending_time_in_seconds > 0.0:
            fade_factor = time_in_seconds / self.__timing.blending_time_in_seconds
        else:
            fade_factor = 1.0
        prev_image = self.__loader.get_image(self.__prev_index)
        assert prev_image is not None
        prev_image.set_alpha(255)
        blit_image_helper(surface, prev_image)
        next_image = self.__loader.get_image(self.__next_index)
        assert next_image is not None
        if fade_factor >= 1.0:
            next_image.set_alpha(255)
        else:
            next_image.set_alpha(round(255.0 * fade_factor))
        blit_image_helper(surface, next_image)

@final
class FixedDiashowSegment(DiashowSegment):
    @staticmethod
    def __get_image_duration_in_seconds(timing: DiashowTiming, image: DiashowImage) -> float:
        if image.rating == 2:
            return timing.star_2_image_duration_in_seconds
        elif image.rating == 3:
            return timing.star_3_image_duration_in_seconds
        elif image.rating == 4:
            return timing.star_4_image_duration_in_seconds
        elif image.rating == 5:
            return timing.star_5_image_duration_in_seconds
        elif image.rating == 1:
            return timing.star_1_image_duration_in_seconds
        else:
            return timing.star_0_image_duration_in_seconds

    def __init__(self, timing: DiashowTiming, loader: ImageLoader, image: DiashowImage, index: int):
        self.__loader = loader
        self.__index = index
        self.__lifetime_in_seconds = self.__get_image_duration_in_seconds(timing, image) - timing.blending_time_in_seconds

    def get_lifetime_in_seconds(self) -> float:
        return self.__lifetime_in_seconds

    def start(self) -> None:
        self.__loader.load_image(self.__index)
        if self.__index >= 0:
            self.__loader.load_image(self.__index + 1)  # pre-load next image

    def update(self, surface: pygame.Surface, time_in_seconds: float) -> None:
        surface.fill((0, 0, 0))
        image = self.__loader.get_image(self.__index)
        assert image is not None
        image.set_alpha(255)
        blit_image_helper(surface, image)

@final
class StopDiashowSegment(DiashowSegment):
    def get_lifetime_in_seconds(self) -> float:
        return 0.0

    def start(self) -> None:
        pass

    def update(self, surface: pygame.Surface, time_in_seconds: float) -> None:
        pass

@final
class DiashowTimelineFactory:
    def __init__(self, timing: DiashowTiming, loader: ImageLoader):
        self.__timing = timing
        self.__loader = loader

    @staticmethod
    def __add_to_timeline(timeline: List[Tuple[float, DiashowSegment]], next_segment: DiashowSegment) -> None:
        if len(timeline) > 0:
            last_time, last_segment = timeline[-1]
            next_time = last_time + last_segment.get_lifetime_in_seconds()
        else:
            next_time = 0.0
        timeline.append((next_time, next_segment))

    def create_timeline(self, images: List[DiashowImage]) -> List[Tuple[float, DiashowSegment]]:
        timeline: List[Tuple[float, DiashowSegment]] = []
        if len(images) > 0:
            self.__add_to_timeline(timeline, StartDiashowSegment(self.__timing, self.__loader))
            for index, image in enumerate(images[:-1]):
                self.__add_to_timeline(timeline, FixedDiashowSegment(self.__timing, self.__loader, image, index))
                self.__add_to_timeline(timeline, CrossFadeDiashowSegment(self.__timing, self.__loader, index, index + 1))
            self.__add_to_timeline(timeline, FixedDiashowSegment(self.__timing, self.__loader, images[-1], -1))
            self.__add_to_timeline(timeline, EndDiashowSegment(self.__timing, self.__loader))
            self.__add_to_timeline(timeline, StopDiashowSegment())
        return timeline

class DiashowController(ABC):
    @abstractmethod
    def set_pause(self, pause: bool) -> None:
        pass

    @abstractmethod
    def goto_prev_image(self) -> None:
        pass

    @abstractmethod
    def goto_next_image(self) -> None:
        pass

    @abstractmethod
    def set_speed(self, speed: Any) -> None:
        pass

    @abstractmethod
    def cancel(self) -> None:
        pass

@final
class InDiashowMenu:
    MENU_SHOW_DURATION_IN_SECONDS = 2.0
    MODE_TEXT_0 = "Wiedergabe"
    MODE_TEXT_1 = "Pause"

    def __init__(self, menu_creator: MenuCreator, diashow_controller: DiashowController, initial_pause: bool, initial_speed: float):
        self.__surface = menu_creator.get_surface()
        self.__end_time_in_seconds = 0.0

        # get initial mode text
        if initial_pause:
            initial_mode_text = self.MODE_TEXT_1
        else:
            initial_mode_text = self.MODE_TEXT_0

        # create menu
        def set_pause(_: Tuple, value: Any) -> None:
            assert isinstance(value, bool)
            diashow_controller.set_pause(value)
        self.__menu = menu_creator.create_menu(
            menu_title="Diashow",
            height=round(float(self.__surface.get_height()) * 0.5),
            width=round(float(self.__surface.get_width()) * 0.5),
            theme_nr=2,
        )
        self.__menu.add.selector("Modus: ", [(self.MODE_TEXT_0, False), (self.MODE_TEXT_1, True)], onchange=set_pause) \
            .set_value(initial_mode_text)
        self.__menu.add.button("Bild zurück", diashow_controller.goto_prev_image)
        self.__menu.add.button("Bild weiter", diashow_controller.goto_next_image)
        self.__menu.add.range_slider("Geschwindigkeit: ", initial_speed, (0.25, 5.0), increment=0.25,
            value_format=lambda x: str(round(x, 2)) + "x", onchange=diashow_controller.set_speed)
        self.__menu.add.vertical_margin(DEFAULT_VERTICAL_MARGIN)
        self.__menu.add.button("Verlassen", diashow_controller.cancel)
        self.__menu.disable()

    def show_menu(self, time_in_seconds: float) -> None:
        self.__end_time_in_seconds = time_in_seconds + self.MENU_SHOW_DURATION_IN_SECONDS
        self.__menu.enable()

    def update(self, time_in_seconds: float, events: List[pygame.event.Event]) -> None:
        if self.__menu.enable():
            if time_in_seconds <= self.__end_time_in_seconds:
                self.__menu.update(events)
                self.__menu.draw(self.__surface)
            else:
                self.__menu.disable()

@final
class DiashowPlayer(DiashowController):
    MENU_WAITING_TIME_IN_SECONDS = 0.5

    def __init__(self, play_node: DiashowNode, timing: DiashowTiming, menu_creator: MenuCreator):
        self.__play_node = play_node
        self.__timing = timing
        self.__menu_creator = menu_creator
        self.__speed = 1.0
        self.__pause = False
        self.__run = True
        self.__diashow_timeline: Optional[List[Tuple[float, DiashowSegment]]] = None
        self.__diashow_timeline_index = -1
        self.__diashow_start_time = 0.0

    def set_pause(self, pause: bool) -> None:
        self.__pause = pause

    def goto_prev_image(self) -> None:
        if self.__diashow_timeline is not None:
            segment_time = get_current_time_since_epoch_in_seconds() - self.__diashow_start_time
            new_diashow_timeline_index = self.__diashow_timeline_index
            while True:
                new_diashow_timeline_index -= 1
                if new_diashow_timeline_index < 0:
                    return
                new_time, new_segment = self.__diashow_timeline[new_diashow_timeline_index]
                if isinstance(new_segment, FixedDiashowSegment):
                    break
            new_start_time_offset = segment_time - new_time
            assert new_start_time_offset >= 0.0
            self.__diashow_timeline_index = new_diashow_timeline_index
            self.__diashow_start_time += new_start_time_offset
            new_segment.start()

    def goto_next_image(self) -> None:
        if self.__diashow_timeline is not None:
            segment_time = get_current_time_since_epoch_in_seconds() - self.__diashow_start_time
            new_diashow_timeline_index = self.__diashow_timeline_index
            while True:
                new_diashow_timeline_index += 1
                if new_diashow_timeline_index >= len(self.__diashow_timeline) - 1:
                    return
                new_time, new_segment = self.__diashow_timeline[new_diashow_timeline_index]
                if isinstance(new_segment, FixedDiashowSegment):
                    break
            new_start_time_offset = new_time - segment_time
            assert new_start_time_offset >= 0.0
            self.__diashow_timeline_index = new_diashow_timeline_index
            self.__diashow_start_time -= new_start_time_offset
            new_segment.start()

    def set_speed(self, speed: Any) -> None:
        self.__speed = speed

    def cancel(self) -> None:
        self.__run = False

    def start(self, surface: pygame.Surface) -> None:
        clock = pygame.time.Clock()

        # clean-up screen
        surface.fill((0, 0, 0))
        pygame.display.flip()

        # prepare diashow
        image_loader = ImageLoader(surface, self.__play_node.images)
        timeline_factory = DiashowTimelineFactory(self.__timing, image_loader)
        self.__diashow_timeline = timeline_factory.create_timeline(self.__play_node.images)
        assert self.__diashow_timeline is not None
        assert len(self.__diashow_timeline) > 0
        assert isinstance(self.__diashow_timeline[-1][1], StopDiashowSegment)
        self.__diashow_timeline[0][1].start()
        menu = InDiashowMenu(
            menu_creator=self.__menu_creator,
            diashow_controller=self,
            initial_pause=self.__pause,
            initial_speed=self.__speed,
        )

        # start diashow
        self.__diashow_timeline_index = 0
        self.__diashow_start_time = get_current_time_since_epoch_in_seconds()
        real_diashow_start_time = self.__diashow_start_time
        previous_time = self.__diashow_start_time
        consider_menu = False
        while self.__run:
            # try to disable mouse visibility
            pygame.mouse.set_visible(False)

            # get current time and update start time if we are in pause mode
            current_time = get_current_time_since_epoch_in_seconds()
            if self.__pause:
                self.__diashow_start_time += current_time - previous_time
            previous_time = current_time

            # get events and show menu
            events = pygame.event.get()
            if consider_menu:
                if events:
                    menu.show_menu(current_time)
            elif (current_time - real_diashow_start_time) >= self.MENU_WAITING_TIME_IN_SECONDS:
                consider_menu = True

            # calculate timeline
            segment_time = current_time - self.__diashow_start_time
            next_time, next_segment = self.__diashow_timeline[self.__diashow_timeline_index + 1]
            index_changed = False
            if segment_time >= next_time:
                if isinstance(next_segment, StopDiashowSegment):
                    break
                self.__diashow_timeline_index += 1
                index_changed = True
                next_segment.start()
            actual_time, actual_segment = self.__diashow_timeline[self.__diashow_timeline_index]
            actual_segment_time = segment_time - actual_time

            # update screen
            actual_segment.update(surface, actual_segment_time)
            menu.update(current_time, events)
            pygame.display.flip()
            if not index_changed:
                clock.tick(FPS)

#-------------------------------------------------------------------------------

def main():
    # read Diashow nodes
    assert os.path.exists(DIASHOW_FOLDER)
    main_node = DiashowReader(DIASHOW_FOLDER).read()
    print_diashow_nodes(main_node)

    # read configuration
    config = create_default_config()

    # start Diashow menu
    pygame.init()
    try:
        surface = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        menu_creator = MenuCreator(surface)
        main_menu = MainMenuCreator(main_node=main_node, config=config).create_main(menu_creator)
        while True:
            main_menu.start(menu_creator)
            play_mode = main_menu.get_play_mode()
            if play_mode == MainMenu.DIASHOW_PLAY_MODE:
                start_menu = DiashowStartMenu(
                    config=config,
                    play_node=main_menu.get_play_node(),
                    hierachy=main_menu.get_hierachy(),
                )
                start_menu.start(menu_creator)
                if not start_menu.is_canceled():
                    player = DiashowPlayer(
                        play_node=start_menu.get_play_node(),
                        timing=start_menu.get_timing(),
                        menu_creator=menu_creator,
                    )
                    player.start(surface)
            elif play_mode == MainMenu.SAVE_CONFIG_MODE:
                print("SAVE")  # TODO
            elif play_mode == MainMenu.EXIT_MODE:
                print()
                print("Bye bye :-) !!!")
                break
    finally:
        pygame.quit()

#-------------------------------------------------------------------------------

if __name__ == "__main__":
    main()
