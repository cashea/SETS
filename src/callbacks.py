import os

from .buildupdater import (
        align_space_frame, clear_captain, clear_doffs, clear_ground_build, clear_ship, clear_traits,
        get_variable_slot_counts, set_skill_unlock_ground, set_skill_unlock_space,
        slot_equipment_item, slot_trait_item, update_equipment_cat, update_starship_traits)
from .build_manager import BuildManager
from .constants import (
        EQUIPMENT_TYPES, PRIMARY_SPECS, SECONDARY_SPECS, SHIP_TEMPLATE, SKILL_POINTS_FOR_RANK,
        SPECIES, SPECIES_TRAITS)
from .datafunctions import (
        load_build_file, load_skill_tree_file, save_build_file, save_skill_tree_file)
from .iofunc import browse_path, get_ship_image, image, open_wiki_page
from .widgets import exec_in_thread

from PySide6.QtCore import Qt


def switch_main_tab(self, index):
    """
    Callback to switch between tabs. Switches build and both sidebar tabs.

    Parameters:
    - :param index: index to switch to (0: space build, 1: ground build, 2: space skills,
    3: ground skills, 4: ship stats, 5: library, 6: settings)
    """
    CHAR_TAB_MAP = {
        0: 0,
        1: 0,
        2: 0,
        3: 0,
        4: 0,  # ship_stats - no character tab needed
        5: 1,
        6: 2
    }
    self.widgets.build_tabber.setCurrentIndex(index)
    self.widgets.sidebar_tabber.setCurrentIndex(index)
    self.widgets.character_tabber.setCurrentIndex(CHAR_TAB_MAP[index])
    if index == 4:
        self.widgets.sidebar.setVisible(False)
    else:
        self.widgets.sidebar.setVisible(True)


def faction_combo_callback(self, new_faction: str):
    """
    Saves new faction to build and changes species selector choices.
    """
    self.build_manager.set_character_data('faction', new_faction)
    self.widgets.character['species'].clear()
    if new_faction != '':
        self.widgets.character['species'].addItems(('', *SPECIES[new_faction]))
    self.build_manager.set_character_data('species', '')
    self.autosave()


def species_combo_callback(self, new_species: str):
    """
    Saves new species to build and changes species trait
    """
    self.build_manager.set_character_data('species', new_species)
    if new_species == 'Alien':
        if not self.building:
            self.build_manager.set_equipment_item('space', 'traits', 10, '')
            self.build_manager.set_equipment_item('ground', 'traits', 10, '')
            self.build_manager.set_equipment_item('space', 'traits', 11, '')
            self.build_manager.set_equipment_item('ground', 'traits', 11, '')
        self.widgets.build['space']['traits'][10].show()
        self.widgets.build['ground']['traits'][10].show()
        self.widgets.build['space']['traits'][11].clear()
        self.widgets.build['ground']['traits'][11].clear()
    else:
        self.widgets.build['space']['traits'][10].hide()
        self.widgets.build['ground']['traits'][10].hide()
        self.widgets.build['space']['traits'][10].clear()
        self.widgets.build['ground']['traits'][10].clear()
        self.build_manager.set_equipment_item('space', 'traits', 10, None)
        self.build_manager.set_equipment_item('ground', 'traits', 10, None)
        new_space_trait = SPECIES_TRAITS['space'].get(new_species, '')
        new_ground_trait = SPECIES_TRAITS['ground'].get(new_species, '')
        if new_space_trait == '':
            self.widgets.build['space']['traits'][11].clear()
            self.build_manager.set_equipment_item('space', 'traits', 11, '')
        else:
            slot_trait_item(self, {'item': new_space_trait}, 'space', 'traits', 11)
        if new_ground_trait == '':
            self.widgets.build['ground']['traits'][11].clear()
            self.build_manager.set_equipment_item('ground', 'traits', 11, '')
        else:
            slot_trait_item(self, {'item': new_ground_trait}, 'ground', 'traits', 11)
    self.autosave()


def spec_combo_callback(self, primary: bool, new_spec: str):
    """
    Saves new spec to build and adjusts choices in other spec combo box.
    """
    if primary:
        self.build_manager.set_character_data('primary_spec', new_spec)
        secondary_combo = self.widgets.character['secondary']
        secondary_specs = set()
        remove_index = None
        for i in range(secondary_combo.count()):
            secondary_specs.add(secondary_combo.itemText(i))
            if secondary_combo.itemText(i) == new_spec and new_spec != '':
                remove_index = i
        if remove_index is not None:
            secondary_combo.removeItem(remove_index)
        secondary_combo.addItems((PRIMARY_SPECS | SECONDARY_SPECS) - secondary_specs)
    else:
        self.build_manager.set_character_data('secondary_spec', new_spec)
        primary_combo = self.widgets.character['primary']
        primary_specs = set()
        remove_index = None
        for i in range(primary_combo.count()):
            primary_specs.add(primary_combo.itemText(i))
            if primary_combo.itemText(i) == new_spec and new_spec != '':
                remove_index = i
        if remove_index is not None:
            primary_combo.removeItem(remove_index)
        primary_combo.addItems(PRIMARY_SPECS - primary_specs)
    self.autosave()


def set_build_item(self, dictionary, key, value, autosave: bool = True):
    """
    Assigns value to dictionary item. Triggers autosave.

    Parameters:
    - :param dictionary: dictionary to use key on
    - :param key: key for the dictionary
    - :param value: value to be assigned to the item
    - :param autosave: set to False to disable autosave
    """
    # Use BuildManager for captain data
    if dictionary is self.build['captain']:
        self.build_manager.set_character_data(key, value)
    else:
        # Fallback to direct assignment for other cases
        dictionary[key] = value
    
    if autosave:
        self.autosave()


def elite_callback(self, state):
    """
    Saves new state and updates build.

    Parameters:
    - :param state: new state of the checkbox
    """
    if state == Qt.CheckState.Checked:
        if not self.building:
            self.build_manager.set_character_data('elite', True)
            self.build_manager.set_equipment_item('space', 'traits', 9, '')
            self.build_manager.set_equipment_item('ground', 'traits', 9, '')
            self.build_manager.set_equipment_item('ground', 'kit_modules', 5, '')
            self.build_manager.set_equipment_item('ground', 'ground_devices', 4, '')
        self.widgets.build['space']['traits'][9].show()
        self.widgets.build['ground']['traits'][9].show()
        self.widgets.build['ground']['kit_modules'][5].show()
        self.widgets.build['ground']['ground_devices'][4].show()
    else:
        if not self.building:
            self.build_manager.set_character_data('elite', False)
            self.build_manager.set_equipment_item('space', 'traits', 9, None)
            self.build_manager.set_equipment_item('ground', 'traits', 9, None)
            self.build_manager.set_equipment_item('ground', 'kit_modules', 5, None)
            self.build_manager.set_equipment_item('ground', 'ground_devices', 4, None)
        self.widgets.build['space']['traits'][9].hide()
        self.widgets.build['space']['traits'][9].clear()
        self.widgets.build['ground']['traits'][9].hide()
        self.widgets.build['ground']['traits'][9].clear()
        self.widgets.build['ground']['kit_modules'][5].hide()
        self.widgets.build['ground']['kit_modules'][5].clear()
        self.widgets.build['ground']['ground_devices'][4].hide()
        self.widgets.build['ground']['ground_devices'][4].clear()
    self.autosave()


def get_boff_abilities(
        self, environment: str, rank: int, boff_id: int) -> set:
    """
    Returns list of boff abilities appropriate for the station described by the parameters.

    Parameters:
    - :param environment: space/ground
    - :param rank: rank of the ability slot
    - :param boff_id: id of the boff
    """
    if environment == 'space':
        profession, specialization = self.build['space']['boff_specs'][boff_id]
        if specialization == 'Temporal Operative':
            specialization = 'Temporal'
    else:
        profession = self.build['ground']['boff_profs'][boff_id]
        specialization = self.build['ground']['boff_specs'][boff_id]
    abilities = self.cache.boff_abilities[environment][profession][rank].keys()
    if specialization != '':
        abilities |= self.cache.boff_abilities[environment][specialization][rank].keys()
    return abilities


def picker(
        self, environment: str, build_key: str, build_subkey: int, button, equipment: bool = False,
        boff_id=None):
    """
    opens dialog to select item, stores it to build and updates item button

    Parameters:
    - :param items: iterable of items available to pick from
    - :param environment: space or ground
    - :param build_key: key to self.build[environment]; for storing picked item
    - :param build_subkey: index of the item within its build_key (category)
    - :param button: reference to the button clicked
    - :param equipment: set to True to show rarity, mark, and modifier selector (optional)
    - :param boff_id: id of the boff; only set when picking boff abilities! (optional)
    """
    modifiers = {}
    if equipment:
        items = self.cache.equipment[build_key].keys()
        modifiers = self.cache.modifiers[build_key]
    elif build_key == 'boffs':
        items = get_boff_abilities(self, environment, build_subkey, boff_id)
    elif build_key == 'traits':
        items = self.cache.traits[environment]['personal'].keys()
    elif build_key == 'starship_traits':
        items = self.cache.starship_traits.keys()
    elif build_key == 'rep_traits':
        items = self.cache.traits[environment]['rep'].keys()
    elif build_key == 'active_rep_traits':
        items = self.cache.traits[environment]['active_rep'].keys()
    else:
        items = []
    if self.settings.value('picker_relative', type=int) == 1:
        pos = button.parent().mapToGlobal(button.pos())
    else:
        pos = None
    new_item = self.picker_window.pick_item(items, pos, equipment, modifiers)
    if new_item is not None:
        widget_storage = self.widgets.build[environment]
        if equipment:
            if 'consoles' in build_key:
                type_ = EQUIPMENT_TYPES[self.cache.equipment[build_key][new_item['item']]['type']]
                for i, mod in enumerate(new_item['modifiers']):
                    if mod not in self.cache.modifiers[type_]:
                        new_item['modifiers'][i] = ''
            slot_equipment_item(self, new_item, environment, build_key, build_subkey)
            # Auto-refresh ship stats when equipment is changed
            if hasattr(self, 'refresh_ship_stats'):
                self.refresh_ship_stats()
        else:
            if boff_id is None:
                slot_trait_item(
                        self, {'item': new_item['item']}, environment, build_key, build_subkey)
                # Auto-refresh ship stats when traits are changed
                if hasattr(self, 'refresh_ship_stats'):
                    self.refresh_ship_stats()
            elif build_key == 'boffs':
                self.build[environment]['boffs'][boff_id][build_subkey] = {
                    'item': new_item['item']
                }
                item_image = image(self, new_item['item'])
                widget_storage['boffs'][boff_id][build_subkey].set_item(item_image)
                widget_storage['boffs'][boff_id][build_subkey].tooltip = (
                        self.cache.boff_abilities['all'][new_item['item']])
        self.autosave()


def boff_profession_callback_space(self, boff_id: int, new_spec: str):
    """
    updates build with newly assigned profession; clears abilities of the old profession
    """
    # to prevent overwriting the build while loading
    if self.building:
        return
    if ' / ' in new_spec:
        profession, specialization = new_spec.split(' / ')
        if specialization == 'Temporal Operative':
            specialization = 'Temporal'
        for ability_num, ability in enumerate(self.build['space']['boffs'][boff_id]):
            if ability is not None and ability != '':
                # Lt. Commander rank contains all abilities
                if ability['item'] not in self.cache.boff_abilities['space'][specialization][2]:
                    self.build['space']['boffs'][boff_id][ability_num] = ''
                    self.widgets.build['space']['boffs'][boff_id][ability_num].clear()
    else:
        profession = new_spec
        specialization = ''
        for ability_num, ability in enumerate(self.build['space']['boffs'][boff_id]):
            if ability is not None and ability != '':
                self.build['space']['boffs'][boff_id][ability_num] = ''
                self.widgets.build['space']['boffs'][boff_id][ability_num].clear()
    self.build['space']['boff_specs'][boff_id] = [profession, specialization]
    self.autosave()


def boff_label_callback_ground(self, boff_id: int, type_: str, new_text: str):
    """
    updates build with newly assigned profession or specialization; clears invalid abilities

    Parameters:
    - :param boff_id: number of the boff station
    - :param type_: "boff_profs" / "boff_specs"
    - :param new_text: new profession / specialization
    """
    if self.building:
        return
    self.build['ground'][type_][boff_id] = new_text
    other_type = 'boff_profs' if type_ == 'boff_specs' else 'boff_specs'
    other_text = self.build['ground'][other_type][boff_id]
    for ability_num, ability in enumerate(self.build['ground']['boffs'][boff_id]):
        if ability is not None and ability != '':
            # Lt. Commander and Commander rank combined contain all abilities
            if (ability['item'] not in self.cache.boff_abilities['ground'][new_text][2]
                    and ability['item'] not in self.cache.boff_abilities['ground'][new_text][3]
                    and ability['item'] not in self.cache.boff_abilities['ground'][other_text][2]
                    and ability['item'] not in self.cache.boff_abilities['ground'][other_text][3]):
                self.build['ground']['boffs'][boff_id][ability_num] = ''
                self.widgets.build['ground']['boffs'][boff_id][ability_num].clear()
    self.autosave()


def select_ship(self):
    """
    Opens ship picker and updates UI to reflect new ship.
    """
    new_ship = self.ship_selector_window.pick_ship()
    if new_ship is None:
        return
    self.building = True
    self.widgets.ship['button'].setText(new_ship)
    ship_data = self.cache.ships[new_ship]
    exec_in_thread(
            self, get_ship_image, self, ship_data['image'],
            result=lambda img: self.widgets.ship['image'].set_image(*img))
    tier = ship_data['tier']
    self.widgets.ship['tier'].clear()
    if tier == 6:
        self.widgets.ship['tier'].addItems(('T6', 'T6-X', 'T6-X2'))
    elif tier == 5:
        self.widgets.ship['tier'].addItems(('T5', 'T5-U', 'T5-X', 'T5-X2'))
    else:
        self.widgets.ship['tier'].addItem(f'T{tier}')
    self.build['space']['ship'] = new_ship
    self.build['space']['tier'] = f'T{tier}'
    if ship_data['equipcannons'] == 'yes':
        self.widgets.ship['dc'].show()
    else:
        self.widgets.ship['dc'].hide()
    align_space_frame(self, ship_data, clear=True)
    self.building = False
    # Auto-refresh ship stats when ship is selected
    if hasattr(self, 'refresh_ship_stats'):
        self.refresh_ship_stats()
    self.autosave()


def tier_callback(self, new_tier: str):
    """
    Updates build according to new tier
    """
    if self.building:
        return
    self.build['space']['tier'] = new_tier
    ship_name = self.build['space']['ship']
    if ship_name == '<Pick Ship>':
        ship_data = SHIP_TEMPLATE
    else:
        ship_data = self.cache.ships[ship_name]
    uni, eng, sci, tac, devices, starship_traits = get_variable_slot_counts(self, ship_data)
    update_equipment_cat(self, 'uni_consoles', uni, can_hide=True)
    update_equipment_cat(self, 'eng_consoles', eng)
    update_equipment_cat(self, 'sci_consoles', sci)
    update_equipment_cat(self, 'tac_consoles', tac)
    update_equipment_cat(self, 'devices', devices)
    update_starship_traits(self, starship_traits)
    self.autosave()


def clear_build_callback(self):
    """
    Clears current build section
    """
    current_tab = self.widgets.build_tabber.currentIndex()
    self.building = True
    if current_tab == 0:
        clear_space_build(self)
    elif current_tab == 1:
        clear_ground_build(self)
    elif current_tab == 2:
        clear_space_skills(self)
    elif current_tab == 3:
        clear_ground_skills(self)
    self.building = False


def clear_space_build(self):
    """
    clears space build
    """
    self.building = True
    clear_ship(self)
    align_space_frame(self, SHIP_TEMPLATE, clear=True)
    clear_traits(self, 'space')
    clear_doffs(self, 'space')
    self.building = False
    self.autosave()


def clear_space_skills(self):
    """
    resets space skill tree
    """
    self.widgets.build['skill_desc']['space'].clear()
    self.build['skill_desc']['space'] = ''
    self.build['space_skills'] = {
        'eng': [False] * 30,
        'sci': [False] * 30,
        'tac': [False] * 30
    }
    self.cache.skills['space_points_total'] = 0
    self.cache.skills['space_points_eng'] = 0
    self.widgets.skill_counts_space['eng'].setText('0')
    self.cache.skills['space_points_sci'] = 0
    self.widgets.skill_counts_space['sci'].setText('0')
    self.cache.skills['space_points_tac'] = 0
    self.widgets.skill_counts_space['tac'].setText('0')
    self.cache.skills['space_points_rank'] = [0] * 5
    for career in ('eng', 'sci', 'tac'):
        for skill_button in self.widgets.build['space_skills'][career]:
            skill_button.clear_overlay()
        self.build['skill_unlocks'][career] = [None] * 5
        for bar_segment in self.widgets.skill_bonus_bars[career]:
            bar_segment.setChecked(False)
        for unlock_button in self.widgets.build['skill_unlocks'][career]:
            unlock_button.clear()


def clear_ground_skills(self):
    """
    resets ground skill tree
    """
    self.widgets.build['skill_desc']['ground'].clear()
    self.build['skill_desc']['ground'] = ''
    self.build['ground_skills'] = [
        [False] * 6,
        [False] * 6,
        [False] * 4,
        [False] * 4
    ]
    self.build['skill_unlocks']['ground'] = [None] * 5
    self.cache.skills['ground_points_total'] = 0
    self.widgets.skill_count_ground.setText('0')
    for skill_subtree in self.widgets.build['ground_skills']:
        for skill_button in skill_subtree:
            skill_button.clear_overlay()
    for unlock_button in self.widgets.build['skill_unlocks']['ground']:
        unlock_button.clear()
    for bar_segment in self.widgets.skill_bonus_bars['ground']:
        bar_segment.setChecked(False)


def clear_all(self):
    """
    Clears space and ground build, skills and captain info
    """
    self.building = True
    clear_space_build(self)
    clear_ground_build(self)
    clear_captain(self)
    clear_space_skills(self)
    clear_ground_skills(self)
    self.building = False
    self.autosave()


def set_ui_scale_setting(self, new_value: int):
    """
    Calculates new_value / 50 and stores it to settings.

    Parameters:
    - :param new_value: 50 times the ui scale percentage
    """
    setting_value = f'{new_value / 50:.2f}'
    self.settings.setValue('ui_scale', setting_value)
    return setting_value


def load_build_callback(self):
    """
    Loads build from file
    """
    load_path = browse_path(
            self, self.config['config_subfolders']['library'],
            'SETS Files (*.json *.png);;JSON file (*.json);;PNG image (*.png);;Any File (*.*)')
    if load_path != '':
        load_build_file(self, load_path)


def load_skills_callback(self):
    """
    Loads skills from file
    """
    load_path = browse_path(
            self, self.config['config_subfolders']['library'],
            'SETS Files (*.json *.png);;JSON file (*.json);;PNG image (*.png);;Any File (*.*)')
    if load_path != '':
        load_skill_tree_file(self, load_path)


def save_build_callback(self):
    """
    Saves build to file
    """
    if self.widgets.ship['button'].text() == '<Pick Ship>':
        proposed_filename = '(Ship Template)'
    else:
        proposed_filename = f"({self.widgets.ship['button'].text()})"
    if self.widgets.ship['name'].text() != '':
        proposed_filename = f"{self.widgets.ship['name'].text()} {proposed_filename}"
    default_path = os.path.join(self.config['config_subfolders']['library'], proposed_filename)
    if self.settings.value('default_save_format') == 'PNG':
        file_types = 'PNG image (*.png);;JSON file (*.json);;Any File (*.*)'
    else:
        file_types = 'JSON file (*.json);;PNG image (*.png);;Any File (*.*)'
    save_path = browse_path(self, default_path, file_types, save=True)
    if save_path != '':
        save_build_file(self, save_path)


def save_skills_callback(self):
    """
    Save skills to file
    """
    default_path = os.path.join(self.config['config_subfolders']['library'], 'Skill Tree')
    if self.settings.value('default_save_format') == 'PNG':
        file_types = 'PNG image (*.png);;JSON file (*.json);;Any File (*.*)'
    else:
        file_types = 'JSON file (*.json);;PNG image (*.png);;Any File (*.*)'
    save_path = browse_path(self, default_path, file_types, save=True)
    if save_path != '':
        save_skill_tree_file(self, save_path)


def ship_info_callback(self):
    """
    Opens wiki page of ship if ship is slotted
    """
    if self.build['space']['ship'] != '<Pick Ship>':
        open_wiki_page(self.cache.ships[self.build['space']['ship']]['Page'])


def open_wiki_context(self):
    """
    Opens wiki page of item in `self.context_menu.clicked_slot`.
    """
    slot = self.context_menu.clicked_slot
    if self.context_menu.clicked_boff_station != -1:
        boff_id = self.context_menu.clicked_boff_station
        item = self.build[slot.environment][slot.type][boff_id][slot.index]
        if item is not None and item != '':
            open_wiki_page(f"Ability: {item['item']}")
        return
    item = self.build[slot.environment][slot.type][slot.index]
    if item is None or item == '':
        return
    if 'traits' in slot.type:
        open_wiki_page(f"Trait: {item['item']}")
    else:
        open_wiki_page(f"{self.cache.equipment[slot.type][item['item']]['Page']}#{item['item']}")


def copy_equipment_item(self):
    """
    Copies equipment item clicked on.
    """
    slot = self.context_menu.clicked_slot
    item = self.build[slot.environment][slot.type][slot.index]
    if item is None or item == '':
        self.context_menu.copied_item = None
        self.context_menu.copied_item_type = None
    else:
        self.context_menu.copied_item = item
        item_type = EQUIPMENT_TYPES[self.cache.equipment[slot.type][item['item']]['type']]
        self.context_menu.copied_item_type = item_type


def paste_equipment_item(self):
    """
    Pastes copied item into clicked slot if slot types are compatible
    """
    slot = self.context_menu.clicked_slot
    copied_type = self.context_menu.copied_item_type
    if slot.type == copied_type:
        slot_equipment_item(
                self, self.context_menu.copied_item, slot.environment, slot.type, slot.index)
    elif copied_type == 'ship_weapon' and (
            slot.type == 'fore_weapons' or slot.type == 'aft_weapons'):
        slot_equipment_item(
                self, self.context_menu.copied_item, slot.environment, slot.type, slot.index)
    elif (copied_type == 'uni_consoles' and 'consoles' in slot.type
            or slot.type == 'uni_consoles' and 'consoles' in copied_type):
        slot_equipment_item(
                self, self.context_menu.copied_item, slot.environment, slot.type, slot.index)
    self.autosave()


def clear_slot(self):
    """
    Clears slot that was rightclicked on.
    """
    slot = self.context_menu.clicked_slot
    if self.context_menu.clicked_boff_station == -1:
        self.widgets.build[slot.environment][slot.type][slot.index].clear()
        self.build[slot.environment][slot.type][slot.index] = ''
    else:
        boff_id = self.context_menu.clicked_boff_station
        self.widgets.build[slot.environment][slot.type][boff_id][slot.index].clear()
        self.build[slot.environment][slot.type][boff_id][slot.index] = ''
    self.autosave()


def edit_equipment_item(self):
    """
    Edit mark, modifiers and rarity of rightclicked item.
    """
    slot = self.context_menu.clicked_slot
    item = self.build[slot.environment][slot.type][slot.index]
    if slot.type == 'fore_weapons' or slot.type == 'aft_weapons':
        item_type = slot.type
    else:
        item_type = EQUIPMENT_TYPES[self.cache.equipment[slot.type][item['item']]['type']]
    modifiers = self.cache.modifiers[item_type]
    new_item = self.edit_window.edit_item(item, modifiers)
    if new_item is not None:
        slot_equipment_item(self, new_item, slot.environment, slot.type, slot.index)
        self.autosave()


def doff_spec_callback(self, new_spec: str, environment: str, doff_id: int):
    """
    Callback for duty officer specialization combobox.

    Parameters:
    - :param new_spec: selected specialization
    - :param environment: "space" / "ground"
    - :param doff_id: index of the doff
    """
    if self.building:
        return
    self.build[environment]['doffs_spec'][doff_id] = new_spec
    self.build[environment]['doffs_variant'][doff_id] = ''
    self.widgets.build[environment]['doffs_variant'][doff_id].clear()
    if new_spec != '':
        variants = getattr(self.cache, f'{environment}_doffs')[new_spec].keys()
        self.widgets.build[environment]['doffs_variant'][doff_id].addItems({''} | variants)
    self.autosave()


def doff_variant_callback(self, new_variant: str, environment: str, doff_id: int):
    """
    Callback for duty officer variant combobox.

    Parameters:
    - :param new_variant: selected variant
    - :param environment: "space" / "ground"
    - :param doff_id: index of the doff
    """
    if self.building:
        return
    self.build[environment]['doffs_variant'][doff_id] = new_variant
    self.autosave()


def toggle_space_skill(self, current_state: bool, career: str, skill_id: int):
    """
    Activates space skill if it's deactivated, deactivates skill if it's activated.

    Parameters:
    - :param current_state: state of the button before toggling
    - :param career: "eng" / "tac" / "sci"
    - :param skill_id: id of the skill node (index in self.build and self.widgets.build)
    """
    if current_state:
        self.widgets.build['space_skills'][career][skill_id].clear_overlay()
        self.widgets.build['space_skills'][career][skill_id].highlight = False
        self.build['space_skills'][career][skill_id] = False
        self.cache.skills['space_points_total'] -= 1
        self.cache.skills[f'space_points_{career}'] -= 1
        self.cache.skills['space_points_rank'][int(skill_id / 6)] -= 1
        segment_index = self.cache.skills[f'space_points_{career}']
        if segment_index < 24:
            self.widgets.skill_bonus_bars[career][segment_index].setChecked(False)
            if segment_index % 5 == 4:
                button_index = (segment_index - 4) // 5
                set_skill_unlock_space(self, career, button_index, None)
            elif segment_index == 23:
                set_skill_unlock_space(self, career, 4, None)
        elif 24 <= segment_index <= 26:
            set_skill_unlock_space(self, career, 4, 0, segment_index)
    else:
        self.widgets.build['space_skills'][career][skill_id].set_overlay(self.cache.overlays.check)
        self.widgets.build['space_skills'][career][skill_id].highlight = True
        self.build['space_skills'][career][skill_id] = True
        self.cache.skills['space_points_total'] += 1
        self.cache.skills[f'space_points_{career}'] += 1
        self.cache.skills['space_points_rank'][int(skill_id / 6)] += 1
        segment_index = self.cache.skills[f'space_points_{career}'] - 1
        if segment_index < 24:
            self.widgets.skill_bonus_bars[career][segment_index].setChecked(True)
            if segment_index % 5 == 4:
                button_index = (segment_index - 4) // 5
                set_skill_unlock_space(self, career, button_index, 0)
            elif segment_index == 23:
                set_skill_unlock_space(self, career, 4, -1, 24)
        elif 24 <= segment_index <= 25:
            set_skill_unlock_space(self, career, 4, 0, segment_index + 1)
        elif segment_index == 26:
            set_skill_unlock_space(self, career, 4, 3, 27)
    self.widgets.skill_counts_space[career].setText(
            str(self.cache.skills[f'space_points_{career}']))
    self.autosave()


def skill_unlock_callback(self, bar: str, unlock_id: int):
    """
    Callback for skill unlock buttons

    Parameters:
    - :param bar: "eng" / "sci" / "tac" / "ground"
    - :param unlock_id: index of the unlock button
    """
    current_state = self.build['skill_unlocks'][bar][unlock_id]
    if current_state is None:
        return
    if bar == 'ground':
        if current_state == 0:
            set_skill_unlock_ground(self, unlock_id, 1)
        elif current_state == 1:
            set_skill_unlock_ground(self, unlock_id, 0)
        self.autosave()
    else:
        if unlock_id < 4:
            if current_state == 0:
                set_skill_unlock_space(self, bar, unlock_id, 1)
            elif current_state == 1:
                set_skill_unlock_space(self, bar, unlock_id, 0)
            self.autosave()
        else:
            points_spent = self.cache.skills[f'space_points_{bar}']
            if 25 <= points_spent <= 26:
                set_skill_unlock_space(self, bar, 4, (current_state + 1) % 3, points_spent)
                self.autosave()


def toggle_ground_skill(self, current_state: bool, skill_group: int, skill_id: int):
    """
    Activates ground skill if it's deactivated, deactivates skill if it's activated.

    Parameters:
    - :param current_state: state of the button before toggling
    - :param skill_group: number [0, 3] identifying the skill group
    - :param skill_id: index of the skill within the group
    """
    if current_state:
        self.widgets.build['ground_skills'][skill_group][skill_id].clear_overlay()
        self.widgets.build['ground_skills'][skill_group][skill_id].highlight = False
        self.build['ground_skills'][skill_group][skill_id] = False
        self.cache.skills['ground_points_total'] -= 1
        segment_index = self.cache.skills['ground_points_total']
        self.widgets.skill_bonus_bars['ground'][segment_index].setChecked(False)
        if segment_index % 2 == 1:
            button_index = (segment_index - 1) // 2
            set_skill_unlock_ground(self, button_index, None)
    else:
        self.widgets.build['ground_skills'][skill_group][skill_id].set_overlay(
                self.cache.overlays.check)
        self.widgets.build['ground_skills'][skill_group][skill_id].highlight = True
        self.build['ground_skills'][skill_group][skill_id] = True
        self.cache.skills['ground_points_total'] += 1
        segment_index = self.cache.skills['ground_points_total'] - 1
        self.widgets.skill_bonus_bars['ground'][segment_index].setChecked(True)
        if segment_index % 2 == 1:
            button_index = (segment_index - 1) // 2
            set_skill_unlock_ground(self, button_index, 0)
    self.widgets.skill_count_ground.setText(str(self.cache.skills['ground_points_total']))
    self.autosave()


def skill_callback_space(self, career: str, skill_id: int, grouping: str):
    """
    Callback for space skill node

    Parameters:
    - :param career: "eng" / "tac" / "sci"
    - :param skill_id: id of the skill node (index in self.build and self.widgets.build)
    - :param grouping: type of skill grouping: "column" / "pair+1" / "separate"
    """
    skill_active = self.build['space_skills'][career][skill_id]
    skill_lvl = skill_id % 3
    skill_rank = int(skill_id / 6)
    if skill_active:  # check for valid deselect
        if (skill_lvl == 2
                or grouping != 'column' and skill_lvl == 1
                or not self.build['space_skills'][career][skill_id + 1]):
            skill_count = sum(self.cache.skills['space_points_rank'][:skill_rank + 1])
            for rank_offset, points_required in enumerate(SKILL_POINTS_FOR_RANK[skill_rank + 1:]):
                if (skill_count - 1 < points_required
                        and self.cache.skills['space_points_total'] - skill_count > 0):
                    return
                skill_count += self.cache.skills['space_points_rank'][skill_rank + rank_offset + 1]
            toggle_space_skill(self, skill_active, career, skill_id)
    else:  # check for valid select
        if 46 > self.cache.skills['space_points_total'] >= SKILL_POINTS_FOR_RANK[skill_rank]:
            if skill_lvl == 0:
                toggle_space_skill(self, skill_active, career, skill_id)
            elif grouping == 'column' and self.build['space_skills'][career][skill_id - 1]:
                toggle_space_skill(self, skill_active, career, skill_id)
            elif grouping != 'column' and self.build['space_skills'][career][skill_id - skill_lvl]:
                toggle_space_skill(self, skill_active, career, skill_id)


def skill_callback_ground(self, skill_group: int, skill_id: int):
    """
    Callback for ground skill node

    Parameters:
    - :param skill_group: number [0, 3] identifying the skill group
    - :param skill_id: index of the skill within the group
    """
    skill_active = self.build['ground_skills'][skill_group][skill_id]
    if skill_active:  # check for valid deselect
        if skill_id == 0 and (
                self.build['ground_skills'][skill_group][1]
                or self.build['ground_skills'][skill_group][2]
                or skill_group <= 1 and self.build['ground_skills'][skill_group][4]):
            return
        elif skill_id % 2 == 0 and self.build['ground_skills'][skill_group][skill_id + 1]:
            return
        toggle_ground_skill(self, skill_active, skill_group, skill_id)
    else:  # check for valid select
        if self.cache.skills['ground_points_total'] < 10:
            if skill_id % 2 == 1 and self.build['ground_skills'][skill_group][skill_id - 1]:
                toggle_ground_skill(self, skill_active, skill_group, skill_id)
            elif skill_id == 0:
                toggle_ground_skill(self, skill_active, skill_group, skill_id)
            elif (skill_id == 2 or skill_id == 4) and self.build['ground_skills'][skill_group][0]:
                toggle_ground_skill(self, skill_active, skill_group, skill_id)


def refresh_ship_stats(self):
    """
    Calculates and displays ship statistics based on selected ship and equipment.
    """
    try:
        # Get selected ship
        ship_name = self.build['space'].get('ship', '')
        
        if not ship_name or ship_name not in self.cache.ships:
            # Clear all stats if no ship selected
            for stat_widget in self.widgets.ship_stats.values():
                stat_widget.setText('--')
            return
        
        ship_data = self.cache.ships[ship_name]
        
        # Base ship stats
        base_stats = {
            'hull': ship_data.get('hull', 0) or 0,
            'shields': ship_data.get('shieldmod', 1.0) or 1.0,
            'turn_rate': ship_data.get('turnrate', 0) or 0,
            'impulse': ship_data.get('impulse', 0) or 0,
            'inertia': ship_data.get('inertia', 0) or 0,
            'power_weapons': ship_data.get('powerweapons', 0) or 0,
            'power_shields': ship_data.get('powershields', 0) or 0,
            'power_engines': ship_data.get('powerengines', 0) or 0,
            'power_auxiliary': ship_data.get('powerauxiliary', 0) or 0,
            'fore_weapons': ship_data.get('fore', 0) or 0,
            'aft_weapons': ship_data.get('aft', 0) or 0,
            'devices': ship_data.get('devices', 0) or 0,
            'hangars': ship_data.get('hangars', 0) or 0
        }
        
        # Display base stats
        print(f"Debug: Available ship_stats widgets: {list(self.widgets.ship_stats.keys())}")
        for stat_name, value in base_stats.items():
            # Convert stat_name to widget key format (e.g., 'power_weapons' -> 'power_weapons')
            widget_key = stat_name
            print(f"Debug: Looking for widget key '{widget_key}' for stat '{stat_name}'")
            if widget_key in self.widgets.ship_stats:
                if isinstance(value, float):
                    self.widgets.ship_stats[widget_key].setText(f"{value:.1f}")
                else:
                    self.widgets.ship_stats[widget_key].setText(str(value))
            else:
                print(f"Debug: Widget key '{widget_key}' not found in ship_stats")
        
        # Calculate equipment bonuses
        equipment_bonuses = self.calculate_equipment_bonuses()
        print(f"Debug: Equipment bonuses: {equipment_bonuses}")
        
        # Calculate trait bonuses
        trait_bonuses = self.calculate_trait_bonuses()
        print(f"Debug: Trait bonuses: {trait_bonuses}")
        
        # Calculate skill bonuses
        skill_bonuses = self.calculate_skill_bonuses()
        print(f"Debug: Skill bonuses: {skill_bonuses}")
        
        # Combine all bonuses
        total_bonuses = {}
        for stat in base_stats.keys():
            total_bonuses[stat] = (
                equipment_bonuses.get(stat, 0) +
                trait_bonuses.get(stat, 0) +
                skill_bonuses.get(stat, 0)
            )
        print(f"Debug: Total bonuses: {total_bonuses}")
        
        # Calculate and display total stats
        for stat_name, base_value in base_stats.items():
            bonus = total_bonuses.get(stat_name, 0)
            total_value = base_value + bonus
            
            # The widget keys have an extra "total_" prefix due to how they're created
            calc_widget_key = f"calc_total_total_{stat_name}"
            if calc_widget_key in self.widgets.ship_stats:
                if isinstance(total_value, float):
                    self.widgets.ship_stats[calc_widget_key].setText(f"{total_value:.1f}")
                else:
                    self.widgets.ship_stats[calc_widget_key].setText(str(total_value))
            else:
                print(f"Debug: Calculated widget key '{calc_widget_key}' not found in ship_stats")
        
        print(f"Ship stats refreshed for: {ship_name}")
        
        # Update stats information text with detailed breakdown
        self._update_stats_info_text(equipment_bonuses, trait_bonuses, skill_bonuses, total_bonuses)
        
    except Exception as e:
        print(f"Error refreshing ship stats: {e}")



    """
    Update the stats information text with detailed breakdown of bonuses.
    """
    try:
        if not hasattr(self.widgets, 'stats_info_text'):
            return
            
        info_text = self.widgets.stats_info_text
        ship_name = self.build['space'].get('ship', '')
        
        # Build detailed info text
        info_lines = [
            f"Ship Statistics for: {ship_name if ship_name else 'No Ship Selected'}",
            "",
            "Base Ship Stats:",
            "• Hull, Shields, Turn Rate, Impulse, Inertia",
            "• Power levels (Weapons, Shields, Engines, Auxiliary)",
            "• Equipment slots (Fore/Aft Weapons, Devices, Hangars)",
            "",
            "Equipment Bonuses:"
        ]
        
        # Add equipment bonuses
        if equipment_bonuses:
            for stat_name, value in equipment_bonuses.items():
                if value != 0:
                    stat_display = stat_name.replace('_', ' ').title()
                    info_lines.append(f"• {stat_display}: +{value:.1f}")
        else:
            info_lines.append("• No equipment bonuses detected")
        
        info_lines.extend([
            "",
            "Trait Bonuses:"
        ])
        
        # Add trait bonuses
        if trait_bonuses:
            for stat_name, value in trait_bonuses.items():
                if value != 0:
                    stat_display = stat_name.replace('_', ' ').title()
                    info_lines.append(f"• {stat_display}: +{value:.1f}")
        else:
            info_lines.append("• No trait bonuses detected")
        
        info_lines.extend([
            "",
            "Skill Bonuses:"
        ])
        
        # Add skill bonuses
        if skill_bonuses:
            for stat_name, value in skill_bonuses.items():
                if value != 0:
                    stat_display = stat_name.replace('_', ' ').title()
                    info_lines.append(f"• {stat_display}: +{value:.1f}")
        else:
            info_lines.append("• No skill bonuses detected")
        
        info_lines.extend([
            "",
            "Total Bonuses:"
        ])
        
        # Add total bonuses
        if total_bonuses:
            for stat_name, value in total_bonuses.items():
                if value != 0:
                    stat_display = stat_name.replace('_', ' ').title()
                    info_lines.append(f"• {stat_display}: +{value:.1f}")
        else:
            info_lines.append("• No total bonuses")
        
        info_lines.extend([
            "",
            "Equipment Modifiers:",
            "• Equipment bonuses are parsed from item tooltips",
            "• Includes bonuses from weapons, consoles, and other equipment",
            "• Modifiers are applied to base ship statistics",
            "",
            "Note: Click 'Refresh Stats' to recalculate when equipment changes."
        ])
        
        info_text.setPlainText('\n'.join(info_lines))
        
    except Exception as e:
        print(f"Error updating stats info text: {e}")


def calculate_equipment_bonuses(self):
    """
    Calculate bonuses from equipped items.
    """
    bonuses = {}
    
    try:
        # Check each equipment slot for bonuses
        equipment_categories = [
            'fore_weapons', 'aft_weapons', 'devices', 'deflector', 'engines', 
            'core', 'shield', 'tac_consoles', 'eng_consoles', 'sci_consoles', 'uni_consoles'
        ]
        
        print(f"Debug: Checking equipment in build: {self.build['space'].keys()}")
        
        for category in equipment_categories:
            if category in self.build['space']:
                print(f"Debug: Checking category {category}: {self.build['space'][category]}")
                for item_data in self.build['space'][category]:
                    if item_data and isinstance(item_data, dict) and 'item' in item_data:
                        item_name = item_data['item']
                        print(f"Debug: Found item {item_name} in {category}")
                        # Check if item exists in the specific category
                        if item_name in self.cache.equipment.get(category, {}):
                            item_info = self.cache.equipment[category][item_name]
                            # Parse tooltip for stat bonuses
                            item_bonuses = self._parse_equipment_bonuses(item_info)
                            print(f"Debug: Item {item_name} bonuses: {item_bonuses}")
                            bonuses.update(item_bonuses)
                        else:
                            # Try to find the item in all equipment categories
                            print(f"Debug: Item {item_name} not found in {category}, searching all categories...")
                            found = False
                            for eq_category, eq_items in self.cache.equipment.items():
                                if item_name in eq_items:
                                    item_info = eq_items[item_name]
                                    item_bonuses = self._parse_equipment_bonuses(item_info)
                                    print(f"Debug: Found {item_name} in {eq_category}, bonuses: {item_bonuses}")
                                    bonuses.update(item_bonuses)
                                    found = True
                                    break
                            if not found:
                                print(f"Debug: Item {item_name} not found in any equipment category")
        
        return bonuses
        
    except Exception as e:
        print(f"Error calculating equipment bonuses: {e}")
        return bonuses

def _parse_equipment_bonuses(self, item_info):
    """
    Parse equipment tooltip to extract stat bonuses.
    """
    bonuses = {}
    
    try:
        # Get the raw item data that was preserved during loading
        if 'raw_data' in item_info:
            raw_data = item_info['raw_data']
            print(f"Debug: Parsing raw data for {item_info.get('name', 'unknown')}")
            
            # Extract bonuses from head and text fields
            for i in range(1, 10):
                head_key = f'head{i}'
                text_key = f'text{i}'
                
                if head_key in raw_data and raw_data[head_key]:
                    head_text = raw_data[head_key]
                    text_content = raw_data.get(text_key, '')
                    
                    # Parse common stat patterns
                    bonuses.update(self._parse_stat_text(head_text, text_content))
        else:
            print(f"Debug: No raw_data found for item {item_info.get('name', 'unknown')}")
        
        return bonuses
        
    except Exception as e:
        print(f"Error parsing equipment bonuses for {item_info.get('name', 'unknown')}: {e}")
        return bonuses

def _parse_stat_text(self, head_text, text_content):
    """
    Parse text content for stat bonuses.
    """
    bonuses = {}
    
    # Common stat patterns to look for
    stat_patterns = {
        'hull': r'(\+?\d+(?:\.\d+)?)\s*(?:percent\s+)?hull',
        'shields': r'(\+?\d+(?:\.\d+)?)\s*(?:percent\s+)?shield',
        'turn_rate': r'(\+?\d+(?:\.\d+)?)\s*(?:percent\s+)?turn\s+rate',
        'impulse': r'(\+?\d+(?:\.\d+)?)\s*(?:percent\s+)?impulse',
        'power_weapons': r'(\+?\d+(?:\.\d+)?)\s*(?:percent\s+)?weapon\s+power',
        'power_shields': r'(\+?\d+(?:\.\d+)?)\s*(?:percent\s+)?shield\s+power',
        'power_engines': r'(\+?\d+(?:\.\d+)?)\s*(?:percent\s+)?engine\s+power',
        'power_auxiliary': r'(\+?\d+(?:\.\d+)?)\s*(?:percent\s+)?auxiliary\s+power'
    }
    
    # Combine head and text content for parsing
    full_text = f"{head_text} {text_content}".lower()
    
    for stat_name, pattern in stat_patterns.items():
        import re
        matches = re.findall(pattern, full_text)
        if matches:
            try:
                # Take the first match and convert to float
                value = float(matches[0])
                bonuses[stat_name] = value
            except (ValueError, IndexError):
                pass
    
    return bonuses


def calculate_trait_bonuses(self):
    """
    Calculate bonuses from selected traits.
    """
    bonuses = {}
    
    try:
        # Check personal traits
        if 'traits' in self.build['space']:
            for trait_data in self.build['space']['traits']:
                if trait_data and isinstance(trait_data, dict) and 'item' in trait_data:
                    trait_name = trait_data['item']
                    # Parse personal trait effects
                    trait_bonuses = self._parse_trait_bonuses(trait_name, 'personal')
                    for stat, bonus in trait_bonuses.items():
                        bonuses[stat] = bonuses.get(stat, 0) + bonus
        
        # Check starship traits
        if 'starship_traits' in self.build['space']:
            for trait_data in self.build['space']['starship_traits']:
                if trait_data and isinstance(trait_data, dict) and 'item' in trait_data:
                    trait_name = trait_data['item']
                    # Parse starship trait effects
                    trait_bonuses = self._parse_trait_bonuses(trait_name, 'starship')
                    for stat, bonus in trait_bonuses.items():
                        bonuses[stat] = bonuses.get(stat, 0) + bonus
        
        return bonuses
        
    except Exception as e:
        print(f"Error calculating trait bonuses: {e}")
        return bonuses

def _parse_trait_bonuses(self, trait_name, trait_type):
    """
    Parse trait effects for stat bonuses.
    """
    bonuses = {}
    
    try:
        if trait_type == 'personal':
            # Look in personal traits
            for env in ['space', 'ground']:
                if trait_name in self.cache.traits.get(env, {}).get('personal', {}):
                    trait_info = self.cache.traits[env]['personal'][trait_name]
                    # Parse trait description for bonuses
                    if 'tooltip' in trait_info:
                        bonuses.update(self._parse_stat_text('', trait_info['tooltip']))
                    break
        elif trait_type == 'starship':
            # Look in starship traits
            if trait_name in self.cache.starship_traits:
                trait_info = self.cache.starship_traits[trait_name]
                # Parse trait description for bonuses
                if 'tooltip' in trait_info:
                    bonuses.update(self._parse_stat_text('', trait_info['tooltip']))
        
        return bonuses
        
    except Exception as e:
        print(f"Error parsing trait bonuses for {trait_name}: {e}")
        return bonuses


def calculate_skill_bonuses(self):
    """
    Calculate bonuses from skill tree.
    """
    bonuses = {}
    
    try:
        # Check space skills for relevant bonuses
        # This would parse the skill tree data for relevant bonuses
        # Simplified for now
        return bonuses
        
    except Exception as e:
        print(f"Error calculating skill bonuses: {e}")
        return bonuses


def _update_stats_info_text(self, equipment_bonuses, trait_bonuses, skill_bonuses, total_bonuses):
    """
    Update the stats information text with detailed breakdown of bonuses.
    """
    try:
        if not hasattr(self.widgets, 'stats_info_text'):
            return
            
        info_text = self.widgets.stats_info_text
        ship_name = self.build['space'].get('ship', '')
        
        # Build detailed info text
        info_lines = [
            f"Ship Statistics for: {ship_name if ship_name else 'No Ship Selected'}",
            "",
            "Base Ship Stats:",
            "• Hull, Shields, Turn Rate, Impulse, Inertia",
            "• Power levels (Weapons, Shields, Engines, Auxiliary)",
            "• Equipment slots (Fore/Aft Weapons, Devices, Hangars)",
            "",
            "Equipment Bonuses:"
        ]
        
        # Add equipment bonuses
        if equipment_bonuses:
            for stat_name, value in equipment_bonuses.items():
                if value != 0:
                    stat_display = stat_name.replace('_', ' ').title()
                    info_lines.append(f"• {stat_display}: +{value:.1f}")
        else:
            info_lines.append("• No equipment bonuses detected")
        
        info_lines.extend([
            "",
            "Trait Bonuses:"
        ])
        
        # Add trait bonuses
        if trait_bonuses:
            for stat_name, value in trait_bonuses.items():
                if value != 0:
                    stat_display = stat_name.replace('_', ' ').title()
                    info_lines.append(f"• {stat_display}: +{value:.1f}")
        else:
            info_lines.append("• No trait bonuses detected")
        
        info_lines.extend([
            "",
            "Skill Bonuses:"
        ])
        
        # Add skill bonuses
        if skill_bonuses:
            for stat_name, value in skill_bonuses.items():
                if value != 0:
                    stat_display = stat_name.replace('_', ' ').title()
                    info_lines.append(f"• {stat_display}: +{value:.1f}")
        else:
            info_lines.append("• No skill bonuses detected")
        
        info_lines.extend([
            "",
            "Total Bonuses:"
        ])
        
        # Add total bonuses
        if total_bonuses:
            for stat_name, value in total_bonuses.items():
                if value != 0:
                    stat_display = stat_name.replace('_', ' ').title()
                    info_lines.append(f"• {stat_display}: +{value:.1f}")
        else:
            info_lines.append("• No total bonuses")
        
        info_lines.extend([
            "",
            "Equipment Modifiers:",
            "• Equipment bonuses are parsed from item tooltips",
            "• Includes bonuses from weapons, consoles, and other equipment",
            "• Modifiers are applied to base ship statistics",
            "",
            "Note: Click 'Refresh Stats' to recalculate when equipment changes."
        ])
        
        info_text.setPlainText('\n'.join(info_lines))
        
    except Exception as e:
        print(f"Error updating stats info text: {e}")
