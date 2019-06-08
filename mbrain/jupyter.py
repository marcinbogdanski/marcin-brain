import re
import json

import nbformat
import nbconvert

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


def get_meta(string):
    """Extract Anki metadata from cell source.
    
    Params:
        string (str): input, e.g. '<!--{"id":"123456789"}--> rest of card.'
    
    Returns:
        dick: metadata as dict, e.g. {"id": "123456789"}
    """
    meta = re.findall(_pattern_meta, string)
    meta = meta[0]                            # only first <!-- -->
    meta = meta.lstrip('<!--').rstrip('-->').strip()
    
    if len(meta) == 0:
        return {}
    else:
        return json.loads(meta)

    
def put_meta(string, anki_id):
    """Replace current Anki metadata with new params.
    
    Params:
        string (str): input, e.g. '<!--Anki meta--> rest of card.'
    
    Returns:
        str: new meta, e.g. '<!--new Anki meta-->'    
    """
    assert isinstance(anki_id, str)
    
    meta_str = json.dumps({"id":anki_id})
    meta_str = '<!-- ' + meta_str + ' -->'
    meta_list = list(meta_str)
    
    string_list = list(string)
    for match in re.finditer(_pattern_meta, string):
        start = match.start()
        end = match.end()
        
        string_list[start:end] = meta_list
        
        break # consider first <!-- --> only
    
    return ''.join(string_list)


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
    head = re.findall(_pattern_head, string)
    return head[0]

def get_head(string):
    """Get Anki head (question) without ** markers
    
    Params:
        string (str): input, e.g. '**Question 1** rest of card.'
    
    Returns:
        str: found head, e.g. 'Question 1'
    """
    head = find_head(string)
    head = head.lstrip('**').rstrip('**').strip()
    return head

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
#                   v----------- pattern (\$\$):   $$ 
#                   | v--------- dot (.): matches any character except line break
#                   | |v-------- plus (+): match one or more of preceeding token
#                   | ||v------- lazy: make preceeding quantifier match as few characters as possible
#                   | |||  v---- pattern (\$\$):   $$
#                   | |||  |
#                 vvvv|||vvvv
_pattern_dodo = r'\$\$.+?\$\$'

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
    for match in re.finditer(_pattern_dodo, string):
        start = match.start()
        end = match.end()
        string_list[start:start+2] = '\['
        string_list[end-2:end] = '\]'
    return ''.join(string_list)

# s = 'ala ma\n$$ ALA $$\nkota ala'
# r = replace_double_dollars(s)
# assert r == 'ala ma\n\[ ALA \]\nkota ala'


# This regex matches in-line non-esscaped dollar:   $some text here$
# Note: escaped dollar \$ won't match
# See: https://stackoverflow.com/questions/11819059/regex-match-character-which-is-not-escaped
#                
#                  v------------ matches if preceding character is not double backslash
#                  |    v------- pattern (\$):   $
#                  |    | v----- dot (.): matches any character except line break
#                  |    | |v---- plus (+): match one or more of preceeding token
#                  |    | ||v--- lazy (?): make preceeding quantifier match as few characters as possible
#                  |    | ||| v- pattern (\$):   $
#                 vvvvv vv|||vv
pattern_sido = r'(?<!\\)\$.+?\$'


def replace_single_dollars(string):
    """Replace all in-line math expressions indicacted by '$'
    
    Why this function:
    Jupyter uses '$' to indicate inline MathJax, e.g. $x=3$, but
    Anki uses '\(' and '\)' for the same purpose, hence this function
    
    Example input line:     some text $ x = 3 $ more text
    Will convert to:        some text \[ x = 3 \[ more text
    Example escaped $       this will cost <span>\$</span>5.99 a piece
    
    Params:
        string (str): input string
    
    Returns:
        str: converted string

    Notes on escaping dollar sign:
     - Jupyter MathJax captures all '$' signs in text, so we have to esape it
     - single backslash escape doensn't work '\$'
     - double backslash, i.e. '\\$', works, but...
       + nbconvert html export has bug, and will sometimes convert '\\$' into '\$'
         and sometimes doesn't, which makes further processsing tricky
     - a way that does seem to work is to escape with '<span>\$</span>', this way:
       + it is ignored by MathJax
       + Jupyter HTML export (via File menu) and nbconvert.HTMLExporter() will produce
         same literal '<span>\$</span>' in ouput HTML, internet browsers seem to
         ignore preceeding '\' so this displayes correctly in browser,
         but Anki displays leading '\', so we need to process further
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

# s = r'adfsa flaj <span>\$</span>30 sdfkla $ x = 3 $ $ y = 2 $.'
# r = replace_single_dollars(s)
# assert r == r'adfsa flaj <span>\$</span>30 sdfkla \( x = 3 \) \( y = 2 \).'

def replace_escaped_dollars(string):
    """Convert '<span>\$</span>' to '$'
    
    Params:
        string (str): input string
    
    Returns:
        str: converted string    
    """
    return string.replace(r'<span>\$</span>', '$')


def process_cell_source(source):
    """Extract meta, head and body from cell['source']
    
    This will:
     - extract and remove metadata from <!--...--> tag
     - extract and remove question from **...** tag
     - convert remaining source as follows:
       + convert double $$..$$ blocks into \[..\]
       + convert single $..$ blocks into \(..\)
       + convert escaped dollars '<span>\$</span>' into '$'
    
    Example source:
        <!--{"id":"1234567890"}-->
        **Example question goes here**
        Some answer goes here
        With escaped dollar <span>\$</span>5.99 price
        Inline latex $x=5$ and latex block
        $$ E = mc^2 $$
        
    Example output:
        META: {"id": "1234567890"}
        HEAD: 'Example question goes here'
        BODY:
            Some answer goes here
            With escaped dollar $5.99 price
            Inline latex \(x=5\) and latex block
            \[ E = mc^2 \]
    
    Params:
        source (str): cell source
    
    Returns:
        meta (dict) - Anki metadata as dict
    """
    meta = get_meta(source)
    source = remove_meta(source)
    head = get_head(source)
    source = remove_head(source)
    source = source.strip()
    
    tmp_nb = nbformat.v4.new_notebook()
    tmp_cell = nbformat.v4.new_markdown_cell(source=source)
    tmp_nb['cells'].append(tmp_cell)
    
    html_exporter = nbconvert.HTMLExporter()
    html_exporter.template_file = 'basic'
    body_raw, _ = html_exporter.from_notebook_node(tmp_nb)
    
    body_nodd = replace_double_dollars(body_raw)
    body_nosd = replace_single_dollars(body_nodd)
    body = replace_escaped_dollars(body_nosd)
    
    return meta, head, body