import re

def is_flashcard(cell):
    """Check if cell is a flashcard
    
    Params:
        cell (dict): must contain 'cell_type' and 'markdown'
    
    Returns:
        bool: True if cell is intendet as flashcard
    """
    assert isinstance(cell, dict)
    
    if cell['cell_type'] != 'markdown':
        return False
    
    source = cell['source']
    
    if isinstance(source, list):
        for line in source:
            if '<!--' in line:
                return True
    elif isinstance(source, str):
        if '<!--' in source:
            return True
        
    return False


# This regex matches pattern:   <!--some text here-->
#
#                   v----------- pattern:   <!--
#                   | v--------- dot: matches any character except line break
#                   | |v-------- star: match zero or more of preceeding token
#                   | ||v------- lazy: make preceeding quantifier match as few characters as possible
#                 vvvv|||vvv---- pattern:   -->
_pattern_meta = r'<!--.*?-->'

def find_meta(string):
    """Find Anki metadata, i.e. first <!--...--> block
    
    Params:
        string (str): input, e.g. '<!--Anki meta--> rest of card.'
    
    Returns:
        str: found meta, e.g. '<!--Anki meta-->'
    """
    meta = re.findall(_pattern_meta, string)
    return meta[0]

def remove_meta(string):
    """Remove Anki metadata, i.e. first <!--...--> section
    
    Params:
        string (str): input, e.g. '<!--Anki meta--> rest of card.'
    
    Returns:
        str: string w/o meta, e.g. ' rest of card.'
    """
    new_string = re.sub(_pattern_meta, '', string)
    return new_string


# This regex matches pattern:   **some text here**
#
#                   v----------- pattern:   ** 
#                   | v--------- dot: matches any character except line break
#                   | |v-------- star: match zero or more of preceeding token
#                   | ||v------- lazy: make preceeding quantifier match as few characters as possible
#                 vvvv|||vvvv--- pattern:   **
_pattern_head = r'\*\*.*?\*\*'

def find_head(string):
    """Find Anki head (question), i.e. first **...** block
    
    Params:
        string (str): input, e.g. '**Question 1** rest of card.'
    
    Returns:
        str: found head, e.g. '**Question 1**'
    """
    meta = re.findall(_pattern_head, string)
    return meta[0]

def remove_head(string):
    """Remove Anki head (question), i.e. first **...** section
    
    Params:
        string (str): input, e.g. '**Question 1** rest of card.'
    
    Returns:
        str: string w/o meta, e.g. ' rest of card.'
    """
    new_string = re.sub(_pattern_head, '', string)
    return new_string



# This regex matches lines in form:   $$some text here$$
# Note: $$ must start and and line
#
#                 v-------------- beginning (^): matches begining of input/line
#                 |  v----------- pattern (\$\$):   $$ 
#                 |  | v--------- dot (.): matches any character except line break
#                 |  | |v-------- plus (+): match one or more of preceeding token
#                 |  | ||  v----- pattern (\$\$):   $$
#                 |  | ||  | v--- end ($): matches end of input/line
#                 |vvvv||vvvv| 
_pattern_dodo = r'^\$\$.+\$\$$'

def replace_double_dollars(string):
    """Replace all math blocks indicated with '$$'
    
    Jupyter uses '$$' to indicate MathJax block, while
    Anki uses '\[' and '\]' for the same purpose
    
    Example input line:     $$ E = mc^2 $$
    Will convert to:        \[ E = mc^2 \[
    
    Note: Jupyter allows MathJax block to span multiple lines,
    but Anki doesn't allow that, so this function only matches
    lines which start and end with '$$'
    
    Params:
        string (str): input string
    
    Returns:
        str: converted string
    """
    string_list = list(string)
    for match in re.finditer(_pattern_dodo, string, flags=re.M):
        start = match.start()
        end = match.end()
        string_list[start:start+2] = '\['
        string_list[end-2:end] = '\]'
    return ''.join(string_list)

# s = 'ala ma\n$$ ALA $$\nkota ala'
# r = replace_double_dollars(s)
# assert r == 'ala ma\n\[ ALA \]\nkota ala'


# This regex matches in-line non-esscaped dollar:   $some text here$
# Note: escaped dollar \\$ won't match
# See: https://stackoverflow.com/questions/11819059/regex-match-character-which-is-not-escaped
#                
#                    v------------ matches if preceding character is not double backslash
#                    |    v------- pattern (\$):   $
#                    |    | v----- dot (.): matches any character except line break
#                    |    | |v---- plus (+): match one or more of preceeding token
#                    |    | ||v--- lazy (?): make preceeding quantifier match as few characters as possible
#                    |    | ||| v- pattern (\$):   $
#                 vvvvvvv vv|||vv
pattern_sido = r'(?<!\\\\)\$.+?\$'


def replace_single_dollars(string):
    """Replace all in-line math expressions indicacted by '$'
    
    Jupyter uses '$' to indicate inline MathJax, while
    Anki uses '\(' and '\)' for the same purpose
    
    Example input line:     some text $ x = 3 $ more text
    Will convert to:        some text \[ x = 3 \[ more text
    
    Note: Jupyter allows to escape dollar sign with double backslash,
    for example \\$50 will be displayed as $50 and wont activate math.
    This behavious is taken into account in this function.
    
    Params:
        string (str): input string
    
    Returns:
        str: converted string
    """
    # Because we replace single char '$' with dual char '\(' and '\)'
    # we have to iterate list backward so we don't offset indices
    matches = []
    for match in re.finditer(pattern_sido, string):
        matches.append(match)
    
    string_list = list(string)
    for match in reversed(matches):
        end = match.end()
        string_list[end-1:end] = ['\\', ')']
        start = match.start()
        string_list[start:start+1] = ['\\', '(']
    return ''.join(string_list)

# s = r'adfsa flaj \\$30 sdfkla $ x = 3 $ $ y = 2 $.'
# r = replace_single_dollars(s)
# assert r == r'adfsa flaj \\$30 sdfkla \( x = 3 \) \( y = 2 \).'

