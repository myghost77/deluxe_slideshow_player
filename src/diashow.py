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
import pygame
import pygame_menu
import exiftool

#-------------------------------------------------------------------------------

DIASHOW_FOLDER = "/media/sf_Exchange/Diashow/"

FILENAME_TAG = "SourceFile"
RATING_TAG = "XMP:Rating"

SCRIPT_PATH, SCRIPT_NAME = os.path.split(__file__)

BACKGROUND_IMAGE = pygame_menu.BaseImage(
    image_path=os.path.join(SCRIPT_PATH, "background.jpg"),
)

DEFAULT_VERTICAL_MARGIN = 35

FPS = 50

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

@dataclass
@final
class DiashowConfig:
    min_time_per_image: TimeValue
    max_time_per_image: TimeValue
    blending_time: Optional[TimeValue]
    weighting: RatingWeighting
    show_duration_in_minutes: float

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

@final
class MenuCreator:
    def __init__(self, surface: pygame.Surface):
        self.__surface = surface
        self.__theme = pygame_menu.themes.THEME_BLUE.copy()
        self.__theme.background_color = BACKGROUND_IMAGE
        self.__theme.selection_color = (212, 212, 212)
        self.__theme.widget_font_shadow = True

    def create_menu(self, menu_title: str) -> pygame_menu.Menu:
        return pygame_menu.Menu(
            title=menu_title,
            height=self.__surface.get_height(),
            width=self.__surface.get_width(),
            theme=self.__theme,
        )

class MenuFactory(ABC):
    @abstractmethod
    def create_menu(self, menu_creator: MenuCreator, menu_title: str, back_label: str) -> pygame_menu.Menu:
        pass

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

    def create_menu(self, menu_creator: MenuCreator, menu_title: str, back_label: str) -> pygame_menu.Menu:
        menu = menu_creator.create_menu(menu_title)
        menu.add.selector("Minimale Standzeit pro Bild: ", TIME_VALUE_SELECTOR_LIST, onchange=self.__set_min_time_per_image) \
            .set_value(self.__diashow_config.min_time_per_image.value.text)
        menu.add.selector("Maximale Standzeit pro Bild: ", TIME_VALUE_SELECTOR_LIST, onchange=self.__set_max_time_per_image) \
            .set_value(self.__diashow_config.max_time_per_image.value.text)
        menu.add.vertical_margin(DEFAULT_VERTICAL_MARGIN)
        menu.add.selector("Überblendzeit zwischen Bildern: ", BLENDING_TIME_VALUE_SELECTOR_LIST, onchange=self.__set_blending_time) \
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
        menu.add.range_slider("Gesamtdauer der Diashow: ", self.__diashow_config.show_duration_in_minutes, (1.0, 120.0), increment=0.5,
            value_format=lambda x: f"{round(x, 1)} Minute(n)", onchange=self.__set_show_duration_in_minutes, width=250)
        menu.add.vertical_margin(DEFAULT_VERTICAL_MARGIN)
        menu.add.button(back_label, pygame_menu.events.BACK)
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

    def create_menu(self, menu_creator: MenuCreator, menu_title: str, back_label: str) -> pygame_menu.Menu:
        default_diashow_config_s_label = "Standard-Einstellungen für kleine Diashows"
        default_diashow_config_m_label = "Standard-Einstellungen für mittelgroße Diashows"
        default_diashow_config_l_label = "Standard-Einstellungen für große Diashows"
        default_diashow_config_x_label = "Standard-Einstellungen für sehr große Diashows"
        menu = menu_creator.create_menu(menu_title)
        menu.add.range_slider("Maximale Anzahl Bilder für kleine Diashows: ", self.__config.max_image_count_for_s, (10.0, 125.0), increment=5.0,
            value_format=lambda x: str(round(x)), onchange=self.__set_max_image_count_for_s)
        menu.add.range_slider("Maximale Anzahl Bilder für mittelgroße Diashows: ", self.__config.max_image_count_for_m, (75.0, 250.0), increment=5.0,
            value_format=lambda x: str(round(x)), onchange=self.__set_max_image_count_for_m)
        menu.add.range_slider("Maximale Anzahl Bilder für große Diashows: ", self.__config.max_image_count_for_l, (125.0, 500.0), increment=5.0,
            value_format=lambda x: str(round(x)), onchange=self.__set_max_image_count_for_l)
        menu.add.vertical_margin(DEFAULT_VERTICAL_MARGIN)
        menu.add.button(default_diashow_config_s_label, self.__default_diashow_options_menu_s.create_menu(
            menu_creator=menu_creator,
            menu_title=default_diashow_config_s_label,
            back_label=back_label,
        ))
        menu.add.button(default_diashow_config_m_label, self.__default_diashow_options_menu_m.create_menu(
            menu_creator=menu_creator,
            menu_title=default_diashow_config_m_label,
            back_label=back_label,
        ))
        menu.add.button(default_diashow_config_l_label, self.__default_diashow_options_menu_l.create_menu(
            menu_creator=menu_creator,
            menu_title=default_diashow_config_l_label,
            back_label=back_label,
        ))
        menu.add.button(default_diashow_config_x_label, self.__default_diashow_options_menu_x.create_menu(
            menu_creator=menu_creator,
            menu_title=default_diashow_config_x_label,
            back_label=back_label,
        ))
        menu.add.vertical_margin(DEFAULT_VERTICAL_MARGIN)
        menu.add.button(back_label, pygame_menu.events.BACK)
        return menu

@final
class MainMenu:
    DIASHOW_PLAY_MODE = "SHOW"
    SAVE_CONFIG_MODE = "SAVE"
    EXIT_MODE = "EXIT"

    def __init__(self, menu: pygame_menu.Menu):
        self.__menu = menu
        self.__play_mode: Optional[str] = None
        self.__show: Optional[DiashowNode] = None

    def enable_diashow(self, show: DiashowNode):
        self.__menu.disable()
        self.__play_mode = self.DIASHOW_PLAY_MODE
        self.__show = show

    def enable_save_options(self):
        self.__menu.disable()
        self.__play_mode = self.SAVE_CONFIG_MODE
        self.__show = None

    def enable_exit(self):
        self.__menu.disable()
        self.__play_mode = self.EXIT_MODE
        self.__show = None

    def get_play_mode(self) -> str:
        assert self.__play_mode is not None
        return self.__play_mode

    def get_show(self) -> DiashowNode:
        assert self.__show is not None
        return self.__show

    def run(self, surface: pygame.Surface) -> str:
        self.__play_mode = None
        self.__show = None
        self.__menu.enable()
        self.__menu.mainloop(surface, fps_limit=FPS)
        if self.__play_mode is None:
            return ""
        else:
            return self.__play_mode

@final
class DiashowMenuFactory(MenuFactory):
    def __init__(self, main_menu: MainMenu, node: DiashowNode, hierachy: List[DiashowNode]):
        self.__main_menu = main_menu
        self.__node = node
        self.__hierachy = hierachy

    def create_menu(self, menu_creator: MenuCreator, menu_title: str, back_label: str) -> pygame_menu.Menu:
        menu = menu_creator.create_menu(menu_title)
        if len(self.__hierachy) > 0:
            for hierachy_node in self.__hierachy:
                menu.add.label(hierachy_node.nodename)
            menu.add.vertical_margin(DEFAULT_VERTICAL_MARGIN)
        if len(self.__node.images) > 0:
            menu.add.button("Start", lambda: self.__main_menu.enable_diashow(self.__node))
            menu.add.vertical_margin(DEFAULT_VERTICAL_MARGIN)
        if len(self.__node.child_nodes) > 0:
            for child_node in self.__node.child_nodes:
                child_diashow_menu_factory = DiashowMenuFactory(
                    main_menu=self.__main_menu,
                    node=child_node,
                    hierachy=self.__hierachy + [child_node],
                )
                menu.add.button(child_node.nodename, child_diashow_menu_factory.create_menu(
                    menu_creator=menu_creator,
                    menu_title=menu_title,
                    back_label=back_label,
                ))
            menu.add.vertical_margin(DEFAULT_VERTICAL_MARGIN)
        menu.add.button(back_label, pygame_menu.events.BACK)
        return menu

@final
class MainMenuCreator:
    def __init__(self, main_node: DiashowNode, config: Config):
        self.__main_node = main_node
        self.__options_menu_factory = OptionsMenuFactory(config)

    def create_main(self, menu_creator: MenuCreator) -> MainMenu:
        select_diashow_label = "Diashow auswählen"
        change_options_label = "Optionen anpassen"
        save_options_label = "Optionen speichern"
        back_label = "Zurück"
        menu = menu_creator.create_menu("Diashow")
        main_menu = MainMenu(menu)
        menu.add.button(select_diashow_label, DiashowMenuFactory(main_menu=main_menu, node=self.__main_node, hierachy=[]).create_menu(
            menu_creator=menu_creator,
            menu_title=select_diashow_label,
            back_label=back_label,
        ))
        menu.add.button(change_options_label, self.__options_menu_factory.create_menu(
            menu_creator=menu_creator,
            menu_title=change_options_label,
            back_label=back_label,
        ))
        menu.add.button(save_options_label, main_menu.enable_save_options)
        menu.add.vertical_margin(DEFAULT_VERTICAL_MARGIN)
        menu.add.button("Verlassen", main_menu.enable_exit)
        return main_menu

#-------------------------------------------------------------------------------

def main():
    # read Diashow nodes
    assert os.path.exists(DIASHOW_FOLDER)
    main_node = Diashow(DIASHOW_FOLDER).read()
    print_diashow_nodes(main_node)

    # read configuration
    config = create_default_config()

    # start Diashow menu
    pygame.init()
    try:
        surface = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        main_menu = MainMenuCreator(main_node=main_node, config=config).create_main(MenuCreator(surface))
        while True:
            play_mode = main_menu.run(surface)
            if play_mode == MainMenu.DIASHOW_PLAY_MODE:
                print(f"SHOW: {main_menu.get_show().nodename}")  # TODO
                continue
            if play_mode == MainMenu.SAVE_CONFIG_MODE:
                print("SAVE")  # TODO
                continue
            if play_mode == MainMenu.EXIT_MODE:
                print()
                print("Bye bye :-) !!!")
                break
    finally:
        pygame.quit()

#-------------------------------------------------------------------------------

if __name__ == "__main__":
    main()
