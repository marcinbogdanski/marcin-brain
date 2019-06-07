

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