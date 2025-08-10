import re
from re import sub as re_sub

from .constants import CAREER_ABBR, RARITY_COLORS, SKILL_PREFIXES, WIKI_URL


def get_tooltip(self, name: str, type_: str, environment: str = 'space') -> str:
    """
    Gets tooltip for item from cache

    Parameters:
    - :param name: name of the item
    - :param type_: type of the item (rep_traits/traits/active_rep_traits/starship_traits)
    - :param environment: space/ground
    """
    try:
        if type_ == 'rep_traits':
            return self.cache.traits[environment]['rep'][name]['tooltip']
        elif type_ == 'traits':
            return self.cache.traits[environment]['personal'][name]['tooltip']
        elif type_ == 'active_rep_traits':
            return self.cache.traits[environment]['active_rep'][name]['tooltip']
        elif type_ == 'starship_traits':
            return self.cache.starship_traits[name]['tooltip']
        else:
            return 'Something is wrong!'
    except KeyError:
        # Return a default tooltip if the trait/item is not found in cache
        return f'Tooltip not available for {name}'


def add_equipment_tooltip_header(self, item: dict, tooltip_body: str, item_type: str) -> str:
    """
    Adds equipment header including name, mark, modifiers, rarity and item type to the tooltip body
    and returns the complete tooltip.

    Parameters:
    - :param item: item to create the tooltip for
    - :param tooltip_body: already created tooltip body
    - :param item_type: type of the item to add to the subtitle
    """
    rarity_color = f'color:{RARITY_COLORS[item["rarity"]]};'
    head_style = self.theme['tooltip']['equipment_name'] + rarity_color
    subhead_style = self.theme['tooltip']['equipment_type_subheader'] + rarity_color
    item_title = item['item']
    if item['mark'] != '' and item['mark'] is not None:
        item_title += ' ' + item['mark']
    mods = ' '.join(mod for mod in item['modifiers'] if mod != '' and mod is not None)
    if mods != '':
        item_title += ' ' + mods
    # Get rarity and item type for subtitle
    rarity = item['rarity']
    item_type_text = item_type.replace('_', ' ').title()
    subtitle = f'{rarity} {item_type_text}'
    
    tooltip = f'<p style="{head_style}">{item_title}</p>'
    tooltip += f'<p style="{subhead_style}">{subtitle}</p>'
    tooltip += tooltip_body
    return tooltip


def format_skill_tooltip(
            self, skill_name: str, skill_data: dict, node_index: int, environment: str) -> str:
    """
    Formats skill tooltip

    Parameters:
    - :param skill_name: name of the skill (without prefix)
    - :param skill_data: contains skill details
    - :param node_index: index of the node within the skill group
    - :param environment: "space" / "ground"
    """
    if environment == 'space':
        if skill_data['grouping'] == 'column':
            prefix = SKILL_PREFIXES[node_index]
            global_description = skill_data['gdesc']
        elif skill_data['grouping'] == 'pair+1':
            if node_index == 1:
                prefix = 'Improved '
            else:
                prefix = ''
            global_description = skill_data['gdesc'][node_index]
        else:
            prefix = ''
            global_description = skill_data['gdesc'][node_index]
        head_style = f"{self.theme['tooltip']['equipment_name']}color:#ffd700;"
        subhead_style = f"{self.theme['tooltip']['equipment_type_subheader']}color:#ffd700;"
        return (
                f"<p style='{head_style}'>{prefix}{skill_name}</p><p style='{subhead_style}'>"
                f"{CAREER_ABBR[skill_data['career']]} {environment.capitalize()} Skill</p>"
                f"<p>{global_description}</p><p>{skill_data['nodes'][node_index]['desc']}</p>")
    elif environment == 'ground':
        head_style = f"{self.theme['tooltip']['equipment_name']}color:#ffd700;"
        subhead_style = f"{self.theme['tooltip']['equipment_type_subheader']}color:#ffd700;"
        return (
                f"<p style='{head_style}'>{skill_name}</p><p style='{subhead_style}'>"
                f"Ground Skill</p>"
                f"<p>{skill_data['gdesc']}</p><p>{skill_data['nodes'][node_index]['desc']}</p>")


def get_skill_unlock_tooltip_ground(self, unlock_id: int, unlock_choice: int):
    """
    gets tooltip for ground unlock from cache and formats it

    Parameters:
    - :param unlock_id: id of the unlock, counted from the unlock with the lowest requirement
    - :param unlock_choice: `0` (first choice; "down") or `1` (second choice; "up")
    """
    unlock = self.cache.skills['ground_unlocks'][unlock_id]['nodes'][unlock_choice]
    head_style = f"{self.theme['tooltip']['equipment_name']}color:#ffd700;"
    subhead_style = f"{self.theme['tooltip']['equipment_type_subheader']}color:#ffd700;"
    return (
            f"<p style='{head_style}'>{unlock['name']}</p><p style='{subhead_style}'>"
            f"Ground Skill</p><p>{unlock['desc']}</p>")


def get_skill_unlock_tooltip_space(self, career: str, unlock_id: int, unlock_choice: int):
    """
    gets tooltip for space unlock from cache and formats it

    Parameters:
    - :param career: "eng" / "sci" / "tac"
    - :param unlock_id: id of the unlock, counted from the unlock with the lowest requirement
    - :param unlock_choice: `0` (first choice; "down") or `1` (second choice; "up")
    """
    unlock = self.cache.skills['space_unlocks'][career][unlock_id]['nodes'][unlock_choice]
    head_style = f"{self.theme['tooltip']['equipment_name']}color:#ffd700;"
    subhead_style = f"{self.theme['tooltip']['equipment_type_subheader']}color:#ffd700;"
    return (
            f"<p style='{head_style}'>{unlock['name']}</p><p style='{subhead_style}'>"
            f"Space Skill</p><p>{unlock['desc']}</p>")


def get_ultimate_skill_unlock_tooltip(self, career: str, unlock_choice: int, enhancements: int):
    """
    gets tooltip for space unlock from cache and formats it

    Parameters:
    - :param unlock_id: id of the unlock, counted from the unlock with the lowest requirement
    - :param unlock_choice: `0` (first choice; "down") or `1` (second choice; "up")
    """
    unlock = self.cache.skills['space_unlocks'][career][4]
    head_style = f"{self.theme['tooltip']['equipment_name']}color:#ffd700;"
    subhead_style = f"{self.theme['tooltip']['equipment_type_subheader']}color:#ffd700;"
    enhancement_style = self.theme['tooltip']['skill_ultimate_name']
    tooltip = (
            f"<p style='{head_style}'>{unlock['name']}</p><p style='{subhead_style}'>"
            f"Space Skill</p><p>{unlock['desc']}</p>")
    if enhancements == 1:
        tooltip += (
                f"<p style='{enhancement_style}'>{unlock['options'][unlock_choice]['name']}</p>"
                f"<p>{unlock['options'][unlock_choice]['desc']}</p>")
    elif enhancements == 2:
        e1 = (unlock_choice - 1) % 3
        e2 = (unlock_choice + 1) % 3
        tooltip += (
                f"<p style='{enhancement_style}'>{unlock['options'][e1]['name']}</p>"
                f"<p>{unlock['options'][e1]['desc']}</p>"
                f"<p style='{enhancement_style}'>{unlock['options'][e2]['name']}</p>"
                f"<p>{unlock['options'][e2]['desc']}</p>")
    elif enhancements != 0:
        for i in range(3):
            tooltip += (
                    f"<p style='{enhancement_style}'>{unlock['options'][i]['name']}</p>"
                    f"<p>{unlock['options'][i]['desc']}</p>")
    return tooltip

# --------------------------------------------------------------------------------------------------
# static functions
# --------------------------------------------------------------------------------------------------


def create_equipment_tooltip(
        item: dict, head_style: str, subhead_style: str, who_style: str, tags) -> str:
    """
    Creates tooltip for equipment from raw item data.

    Parameters:
    - :param item: item data (from cargo table)
    - :param head_style: css style for head
    - :param subhead_style: css style for subhead
    - :param who_style: css style for ship/career/... restriction information
    - :param tags: css styles for the wikitext parser
    """
    tooltip = ''
    if item['who'] is not None:
        tooltip += f"<p style='{who_style}'>{item['who']}</p>"
    for i in range(1, 10, 1):
        if item[f'head{i}'] is not None:
            processed_text = process_placeholder_text(dewikify(item[f'head{i}']), item)
            tooltip += f"<p style='{head_style}'>{format_wikitext(processed_text)}</p>"
        if item[f'subhead{i}'] is not None:
            processed_text = process_placeholder_text(dewikify(item[f'subhead{i}']), item)
            tooltip += (
                    f"<p style='{subhead_style}'>"
                    f"{format_wikitext(processed_text)}</p>")
        if item[f'text{i}'] is not None:
            processed_text = process_placeholder_text(dewikify(item[f'text{i}']), item)
            tooltip += (
                    f"<p style='margin:0'>"
                    f"{parse_wikitext(processed_text, tags)}</p>")
    return tooltip


def create_trait_tooltip(
        name: str, description: str, type_: str, environment: str, head_style: str,
        subhead_style: str, tags) -> str:
    """
    Creates tooltip for trait from trait description.

    Parameters:
    - :param name: name of the trait
    - :param description: description of the trait
    - :param type_: type of the trait; one of "personal", "rep", "active_rep"
    - :param environment: "space" / "ground"
    - :param head_style: css style for head
    - :param subhead_style: css style for subhead
    - :param tags: css styles for the wikitext parser
    """
    if type_ == 'personal':
        tooltip = (
                f"<p style='{head_style}'>{name}</p><p style='{subhead_style}'>"
                f"Personal {environment.capitalize()} Trait</p><p>"
                f"{parse_wikitext(dewikify(description), tags)}</p>")
    elif type_ == 'rep':
        tooltip = (
                f"<p style='{head_style}'>{name}</p><p style='{subhead_style}'>"
                f"{environment.capitalize()} Reputation Trait</p><p>"
                f"{parse_wikitext(dewikify(description), tags)}</p>")
    elif type_ == 'active_rep':
        tooltip = (
                f"<p style='{head_style}'>{name}</p><p style='{subhead_style}'>"
                f"Active {environment.capitalize()} Reputation Trait</p><p style='margin:0'>"
                f"{parse_wikitext(dewikify(description), tags)}</p>")
    else:
        tooltip = ''
    return tooltip


def parse_wikitext(text: str, tags) -> str:
    """
    Converts wikitext lists and indentation into the html subset Qt uses. Also converts inline
    formatting

    Parameters:
    - :param text: contains the text to be formatted
    - :param tags: namedtuple with elements ul, li, indent containing css style of tags
    """
    if text is None:
        return ''
    text = text.replace('\n: *', '\n**')
    text = text.replace(':*', '**')
    html = ''
    ul_tag = f"<ul style='{tags.ul}'>"
    in_list = 0
    for textblock in text.splitlines():
        if textblock.startswith(':'):
            if in_list != 0:
                html += '</ul>' * in_list
            html += f"<p style='{tags.indent}'>{textblock[1:]}</p>"
        elif textblock.startswith('*'):
            if textblock.startswith('***') and in_list < 3:
                html += ul_tag * (3 - in_list)
                in_list = 3
            elif textblock.startswith('**'):
                if in_list < 2:
                    html += ul_tag * (2 - in_list)
                elif in_list == 3:
                    html += '</ul>'
                in_list = 2
            else:
                if in_list == 0:
                    html += ul_tag
                else:
                    html += '</ul>' * (in_list - 1)
                in_list = 1
            html += f"<li style='{tags.li}'>{textblock[in_list:]}</li>"
        else:
            if in_list != 0:
                html += '</ul>' * in_list
            if html.endswith('>') or len(html) == 0:
                html += textblock
            else:
                html += f"<br>{textblock}"
    if in_list != 0:
        html += '</ul>' * in_list

    return format_wikitext(html)


def format_wikitext(text: str) -> str:
    """
    Converts inline formatting from wikitext to html
    """
    bolditalic_html = ''
    splitted = text.split("'''''")
    for i in range(0, len(splitted) - 2, 2):
        bolditalic_html += f"{splitted[i]}<b><i>{splitted[i + 1]}</i></b>"
    bolditalic_html += splitted[-1]
    bold = ''
    splitted = bolditalic_html.split("'''")
    for i in range(0, len(splitted) - 2, 2):
        bold += f"{splitted[i]}<b>{splitted[i + 1]}</b>"
    bold += splitted[-1]
    italic = ''
    splitted = bold.split("''")
    for i in range(0, len(splitted) - 2, 2):
        italic += f"{splitted[i]}<i>{splitted[i + 1]}</i>"
    italic += splitted[-1]
    return italic


def dewikify(text: str, remove_formatting: bool = False) -> str:
    """
    Unescapes wiki formatting.

    Parameters:
    - :param text: text to dewikify
    - :param remove_formatting: set to True to remove all formatting tags (HTML and wiki markup)
    """
    if text is None or text == '':
        return ''
    # text = unescape(unescape(text))
    # text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&#34;', '"')
    # text = text.replace('&#39;', "'")
    # text = text.replace('&#039;', "'")
    text = text.replace('&#91;', '[')
    text = text.replace('&#93;', ']')
    text = text.replace('&quot;', '"')
    # \u007f'&quot;`UNIQ--nowiki-00000000-QINU`&quot;'\u007f
    if '\u007f' in text:
        text = re_sub('\u007f\'"`UNIQ--nowiki-[A-Z0-9]*?-QINU`"\'\u007f', '*', text)
        text = text.replace('\u007f', '')
    if '[[' in text:
        text = re_sub(r'\[\[(.*?\|)?(.*?)\]\]', r'\2', text)
    text = text.replace('[[', '').replace(']]', '')
    text = text.replace('{{lc: ', '').replace('{{lc:', '')
    text = text.replace('{{ucfirst: ', '').replace('{{ucfirst:', '')
    text = text.replace('{{', '').replace('}}', '')
    text = text.replace('&#42;', '*')
    # text = text.replace('\n', '<br>')
    # text = text.replace('<br>', '\n').replace('<br/>', '\n').replace('<br />', '\n')
    if remove_formatting:
        text = re_sub('<.*?>', '', text)
        text = text.replace("'", '')
    return text


def compensate_json(text: str) -> str:
    """
    Unescapes known HTML entities in json text.

    Parameters:
    - :param text: text to compensate
    """
    text = text.replace('&amp;', '&')
    text = text.replace('&#039;', "'")
    text = text.replace('&#39;', "'")
    return text


def process_placeholder_text(text: str, item: dict) -> str:
    """
    Process text to replace placeholder values with resolved values.
    
    Parameters:
    - :param text: text that may contain placeholders
    - :param item: item data containing rarity and other context
    
    Returns:
    - Processed text with placeholders replaced
    """
    if not text:
        return text
    
    # Get rarity from item
    rarity = item.get('rarity', 'Common')
    item_name = item.get('item', '')
    
    # Check if we have a placeholder resolver available
    try:
        # Import here to avoid circular imports
        from .placeholder_resolver import PlaceholderResolver
        
        # Create resolver instance (this should ideally be passed in or stored globally)
        # For now, we'll create a temporary one
        resolver = PlaceholderResolver(None)  # We'll need to pass the cache
        
        # Look for placeholder patterns
        placeholder_patterns = [
            r'\+__% Flight Turn Rate',
            r'\+__% Turn Rate', 
            r'__% Flight Turn Rate',
            r'__% Turn Rate',
            r'\+__% Impulse',
            r'__% Impulse',
            r'\+__% Hull',
            r'__% Hull',
            r'\+__% Shield',
            r'__% Shield'
        ]
        
        processed_text = text
        for pattern in placeholder_patterns:
            if re.search(pattern, processed_text, flags=re.IGNORECASE):
                print(f"Debug: Found placeholder pattern '{pattern}' in text: '{text[:100]}...'")
                
                # For now, use the existing replacement functions
                if 'turn rate' in pattern.lower():
                    replacement = get_rcs_turn_rate_replacement(rarity)
                elif 'impulse' in pattern.lower():
                    replacement = get_impulse_replacement(rarity)
                elif 'hull' in pattern.lower():
                    replacement = get_hull_replacement(rarity)
                elif 'shield' in pattern.lower():
                    replacement = get_shield_replacement(rarity)
                else:
                    replacement = "Unknown"
                
                print(f"Debug: Replacing with: '{replacement}'")
                processed_text = re.sub(pattern, replacement, processed_text, flags=re.IGNORECASE)
                print(f"Debug: Result: '{processed_text[:100]}...'")
        
        return processed_text
        
    except ImportError:
        # Fallback to original method if resolver is not available
        print("Debug: PlaceholderResolver not available, using fallback method")
        return _process_placeholder_text_fallback(text, item)


def get_rcs_turn_rate_replacement(rarity: str) -> str:
    """Get turn rate replacement based on rarity"""
    rarity_scaling = {
        'Common': 1.0,
        'Uncommon': 1.2,
        'Rare': 1.5,
        'Very Rare': 2.0,
        'Ultra Rare': 2.5,
        'Epic': 3.0
    }
    scaling = rarity_scaling.get(rarity, 1.0)
    base_value = 15.0 * scaling
    return f"+{base_value:.1f}% Flight Turn Rate"


def get_impulse_replacement(rarity: str) -> str:
    """Get impulse replacement based on rarity"""
    rarity_scaling = {
        'Common': 1.0,
        'Uncommon': 1.2,
        'Rare': 1.5,
        'Very Rare': 2.0,
        'Ultra Rare': 2.5,
        'Epic': 3.0
    }
    scaling = rarity_scaling.get(rarity, 1.0)
    base_value = 10.0 * scaling
    return f"+{base_value:.1f}% Impulse"


def get_hull_replacement(rarity: str) -> str:
    """Get hull replacement based on rarity"""
    rarity_scaling = {
        'Common': 1.0,
        'Uncommon': 1.2,
        'Rare': 1.5,
        'Very Rare': 2.0,
        'Ultra Rare': 2.5,
        'Epic': 3.0
    }
    scaling = rarity_scaling.get(rarity, 1.0)
    base_value = 5.0 * scaling
    return f"+{base_value:.1f}% Hull"


def get_shield_replacement(rarity: str) -> str:
    """Get shield replacement based on rarity"""
    rarity_scaling = {
        'Common': 1.0,
        'Uncommon': 1.2,
        'Rare': 1.5,
        'Very Rare': 2.0,
        'Ultra Rare': 2.5,
        'Epic': 3.0
    }
    scaling = rarity_scaling.get(rarity, 1.0)
    base_value = 5.0 * scaling
    return f"+{base_value:.1f}% Shield"


def sanitize_equipment_name(name: str) -> str:
    """
    Cleans equipment name.

    Parameters:
    - :param name: name to clean
    """
    name = name.replace('&quot;', '"')
    name = name.replace('&#34;', '"')
    if '∞' in name:
        name, _ = name.split('∞', 1)
    if 'Mk X' in name:
        name, _ = name.split('Mk X', 1)
    if 'MK X' in name:
        name, _ = name.split('MK X', 1)
    if '[' in name:
        name, _ = name.split('[', 1)
    if name[-2:] == '-S':
        name = name[:-2]
    return name.strip()


def wiki_url(page_name: str, prefix: str = ''):
    return (WIKI_URL + prefix + page_name).replace(' ', '_')


def _process_placeholder_text_fallback(text: str, item: dict) -> str:
    """
    Fallback method for processing placeholder text when resolver is not available.
    
    Parameters:
    - :param text: text that may contain placeholders
    - :param item: item data containing rarity and other context
    
    Returns:
    - Processed text with placeholders replaced
    """
    if not text:
        return text
    
    # Get rarity from item
    rarity = item.get('rarity', 'Common')
    
    # Define placeholder patterns and their replacements
    placeholder_patterns = [
        (r'\+__% Flight Turn Rate', get_rcs_turn_rate_replacement(rarity)),
        (r'\+__% Turn Rate', get_rcs_turn_rate_replacement(rarity)),
        (r'__% Flight Turn Rate', get_rcs_turn_rate_replacement(rarity)),
        (r'__% Turn Rate', get_rcs_turn_rate_replacement(rarity)),
        (r'\+__% Impulse', get_impulse_replacement(rarity)),
        (r'__% Impulse', get_impulse_replacement(rarity)),
        (r'\+__% Hull', get_hull_replacement(rarity)),
        (r'__% Hull', get_hull_replacement(rarity)),
        (r'\+__% Shield', get_shield_replacement(rarity)),
        (r'__% Shield', get_shield_replacement(rarity))
    ]
    
    processed_text = text
    for pattern, replacement in placeholder_patterns:
        if re.search(pattern, processed_text, flags=re.IGNORECASE):
            print(f"Debug: Found placeholder pattern '{pattern}' in text: '{text[:100]}...'")
            print(f"Debug: Replacing with: '{replacement}'")
            processed_text = re.sub(pattern, replacement, processed_text, flags=re.IGNORECASE)
            print(f"Debug: Result: '{processed_text[:100]}...'")
    
    return processed_text
