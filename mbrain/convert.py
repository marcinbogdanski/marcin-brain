from .jupyter import put_meta

from .anki import anki_get_note
from .anki import anki_add_note
from .anki import anki_update_note
from .anki import anki_get_media
from .anki import anki_add_or_replace_media


class Command:
    """Thin wrapper around command parameters.
    
    Attributes:
        cmd (str): one of 'add', 'add2', 'update'
        id (str): Anki note ID
        head (str): note question
        body (str): note answer
        deck (str): Anki deck name
        cell (nbformat.notebooknode.NotebookNode): whole cell extracted from Jupyter
        attachments (dict): dict returned from get_attachments() function
    """
    def __init__(self, cmd, id_, head, body, deck=None, cell=None, attachments=None):
        self.cmd = cmd
        self.id = id_
        self.head = head
        self.body = body
        self.deck = deck
        self.cell = cell
        self.attachments = attachments

        
def figure_out_command(meta, head, body, note_ids):
    """Based on available information, estabilish which command to run.
    
    Commands possible are:
     - if 'meta' has no 'id', then execude ADD command
     - if 'meta' has 'id', but 'id' is not in Anki, then execute ADD2
     - if 'meta' has valid 'id', then pull card from Anki and if
       there is a difference, then execute UPDATE
       
    Params:
        meta (str), head (str), body (str): as returned from process_cell() function
        note_ids (list-of-str): list of note IDs in Anki deck
        
    Returns:
        Command: object describing action to perform on Anki DB
    """
    if 'id' not in meta:
        # This note has empty <!---->, meaning it was just added in Jupyter
        cmd = Command('add', None, head, body)
    else:
        # Get note Anki ID
        id_ = meta['id']

        if id_ not in note_ids:
            # card was probably manually deleted from Anki, recreate it
            cmd = Command('add2', None, head, body)
        else:
            # ID exists in database

            front, back = anki_get_note(id_)
            if front != head or back != body:
                cmd = Command('update', id_, head, body)
            else:
                cmd = None
    return cmd


def execute_command(cmd):
    """Execute give command on Anki database.
    
    Params:
        cmd (Command): object describing action to perform on Anki DB
    """
    assert cmd.deck is not None
    assert cmd.cell is not None
    assert cmd.attachments is not None
    if cmd.cmd in ['add', 'add2']:
        id_ = anki_add_note(cmd.deck, cmd.head, cmd.body)
        new_meta = put_meta(cmd.cell.source, id_)
        cmd.cell.source = new_meta
        for name, (key, value) in cmd.attachments.items():
            if anki_get_media(key) is None:
                anki_add_or_replace_media(key, value)
    elif cmd.cmd == 'update':
        anki_update_note(cmd.id, cmd.head, cmd.body)
    else:
        raise ValueError(f'Unknown command: {cmd.cmd}')