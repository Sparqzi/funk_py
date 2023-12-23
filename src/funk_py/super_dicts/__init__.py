from modularity.logging import make_logger


main_logger = make_logger('super_dicts', 'SUPER_DICT_LOGGER',
                          default_level='warning', TRACE=5)


from super_dicts.drop_none_dict import DropNoneDict      # abbr. as DnD  # noqa
from super_dicts.multi_key_dict import MultiKeyDict      # abbr. as MkD  # noqa
from super_dicts.list_dict import ListDict               # abbr. as Ld   # noqa
from super_dicts.multi_value_dict import MultiValueDict  # abbr. as MvD  # noqa
from super_dicts.windowed_list import WindowedList       # abbr. as Wl   # noqa
