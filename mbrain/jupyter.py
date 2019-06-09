import re
import json
import hashlib
import collections

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


def _extract_attachment_name(string):
    """Get attachment name from markdown ![title](name) format
    
    Params:
        string (str): Markdown attachment in format '![TITLE](ATTACHMENT)'
        
    Return:
        string (str): Extracted attachment name, i.e. 'ATTACHMENT'
    """
    
    # This pattern will match '![XXXXX](attachment:'
    # this is used to extract image name
    _pattern = r'\!\[.*?\]\(attachment:'
    result = re.sub(_pattern, '', string).rstrip(')')
    return result


KeyValue = collections.namedtuple('KeyValue', ('key', 'value'))


def get_attachments(cell):
    """Extract all valid attachments from the cell.
    
    For attachment to be extracted, following conditions need to be met:
     - cell.source must contain following tag: ![TITLE](ATTACHMENT_NAME)
       where TITLE and ATTACHMENT_NAME are any strings (TITLE can be 0-length)
     - cell['attachments']['ATTACHMENT_NAME']['SOME_TYPE'] must contain base64 data
       and where SOME_TYPE is any string, usually 'image/png'
     - if first condition is met, but not the second, then exception is raised
    
    Params:
        cell (nbformat.notebooknode.NotebookNode): Jupyter Cell
    
    Returns:
        dict (ATTACHMENT_NAME -> (SHA256, VALUE)): with following members:
            ATTACHMENT_NAME (str): name of attachment, as in Jupyter markdown cell
            SHA256 (str): SHA256 hexdigest of VALUE below
            VALUE (str): base64 encoded data, copy-pasted from Jupyter cell attachment
    """
    
    # This pattern will match '![XXXXX](attachment:YYYYY)'
    # where XXX is image title, usually 'image.png'
    # any YYY is attachment name, usually also 'image.png'
    _pattern_atta = r'\!\[.*?\]\(attachment:.+?\)'
    
    attachments_raw = re.findall(_pattern_atta, cell.source)
    # >>> print(attachments_raw)
    # ['![image.png](attachment:image.png)']
    
    attachment_names = []
    for att_raw in attachments_raw:
        attachment_names.append(_extract_attachment_name(att_raw))
    # >>> print(attachment_names)
    # ['image.png']
    
    if len(attachment_names) == 0:
        return {}  #  nothing more to do here
    
    # If cell is well formed, then it should contain following key with base64 value:
    # cell['attachments']['image.png']['image/png'] -> 'iVBORw0KGgoAAAANS...'

    attachment_sha256_values = {}  # <- this is returned from function

    if 'attachments' in cell:
        for name in attachment_names:
            if name in cell['attachments']:
                if 'image/png' in cell['attachments'][name]:
                    value = cell['attachments'][name]['image/png']
                    sha256 = hashlib.sha256(value.encode()).hexdigest()
                    key = sha256
                    attachment_sha256_values[name] = KeyValue(key, value)
                else:
                    raise ValueError(f"Attachment {name} is not a 'image/png'???")
            else:
                raise ValueError(f"Attachment {name} not found in Jupyter cell attachments")
    else:
        raise ValueError("Cell has markdown image ![](), but no cell has no 'attachments' in Jupyter?")
        
    # >>> print(attachment_sha256_values)
    # {'image.png': KeyValue(key='9ea02ea....png', value='iVBORw...')}
    
    return attachment_sha256_values


def replace_div_style(string_html):
    """Add left-align css style
    
    Params:
        string_html (str): cell converted to html
        
    Returns:
        str: new html with tag replaced
    """
    
    pattern = '<div class="inner_cell">'
    target =  '<div class="inner_cell" style="text-align: left">'
    return re.sub(pattern, target, string_html)


def replace_image_tags(string_html, attachment_name, attachment_sha256):
    """Replace <img> tag in html with sha256
    
    This function will perform following substitutions in string_html:
     - input:  '<img src="attachment:ATTACHMENT_NAME" alt="XXX">'
     - output: '<img src="ATTACHMENT_SHA256">'
     - where ATTACHMENT_NAME and ATTACHMENT_SHA256 are params to this funciton
    
    Params:
        string_html (str): cell converted to html
        attachment_name (str): name of attachment, use get_attachments() to acquire
        attachment_sha256 (str): sha256 hexdigest, use get_attachments() to acquire
        
    Returns:
        str: new html with one or more tags replaced
    """
    
    # This will match if string alphanumeric with optional dot
    # If string contains any other characters this will not match
    pattern = r'^[a-zA-Z0-9.]+$'
    res = re.match(pattern, attachment_name)
    if res is None:
        raise ValueError(f'Attachment name ({attachment_name})must be alphanumerc with optional dots.')
    
    # If we want to use name in regex, we have to escape any dots
    a = attachment_name.replace('.', '\.')
    
    # This will match '<img src="attachment:ATTACHMENT_NAME" alt="XXX">'
    # Where ATTACHMENT_NAME is param passed to this function
    # and XXX is any string
    pattern = f'<img src="attachment:{a}" alt=".*?">'
    
    # Above pattern will be replaced with this
    target = f'<img src="{attachment_sha256}">'
    
    return re.sub(pattern, target, string_html)





def process_cell(cell):
    """Extract meta, head, body and attachments from Jupyter cell
    
    This will:
     - extract and remove metadata from <!--...--> tag from cell.source
     - extract and remove question from **...** tag from cell.source
     - extract any attachments mentioned in ![...](...) tags in cell.source
     - convert remaining Markdown cell.source into HTML
     - convert HTML as follows:
       + convert double $$..$$ blocks into \[..\]
       + convert single $..$ blocks into \(..\)
       + convert escaped dollars '<span>\$</span>' into '$'
       + replace <img src="attachment:..."> with <img src="SHA256">
    
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
    
    assert isinstance(cell, nbformat.notebooknode.NotebookNode)
    source = cell.source
    
    # Extract and remove <!--...-->
    meta = get_meta(source)
    source = remove_meta(source)
    
    # Extract and remove **...**
    head = get_head(source)
    source = remove_head(source)
    source = source.strip()
    
    # Extract attachments
    attachments = get_attachments(cell)
    
    # Convert to HTML
    tmp_nb = nbformat.v4.new_notebook()
    tmp_cell = nbformat.v4.new_markdown_cell(source=source)
    tmp_nb['cells'].append(tmp_cell)
    html_exporter = nbconvert.HTMLExporter()
    html_exporter.template_file = 'basic'
    body_raw, _ = html_exporter.from_notebook_node(tmp_nb)
    
    # Replace $$...$$ with \[...\]
    body_nodd = replace_double_dollars(body_raw)
    
    # Replace $...$ with \(...\)
    body_nosd = replace_single_dollars(body_nodd)
    
    # Replace <span>\$</span> with $
    body_noed = replace_escaped_dollars(body_nosd)
    
    # Add style="text-align: left" to <div class="inner_cell">
    body = replace_div_style(body_noed)
    
    # Replace <img src="attachment:..."> with <img src="SHA256">
    for name, (sha256, value) in attachments.items():
        body = replace_image_tags(body, name, sha256)
    
    return meta, head, body, attachments