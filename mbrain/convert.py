import os
import glob

import nbformat

from .jupyter import put_meta

from .anki import anki_get_note
from .anki import anki_add_note
from .anki import anki_update_note
from .anki import anki_get_media
from .anki import anki_add_or_replace_media
from .anki import anki_find_notes
from .jupyter import is_flashcard
from .jupyter import process_cell

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
        notebook_filepath (str): path to notebook filename containing cell node
        notebook_changed (bool): True means cell metadata changed and .ipynb file needs update
        notebook_may_change (bool): True means command can may requrie update to .ipynb file
    """
    def __init__(self, cmd, id_, head, body, deck=None,
                 filepath=None, notebook=None, cell=None, attachments=None):
        assert isinstance(cmd, str)
        assert cmd in {'noop', 'add', 'add2', 'update'}
        
        self.cmd = cmd
        self.id = id_
        self.head = head
        self.body = body
        self.deck = deck
        self.cell = cell
        self.attachments = attachments
        
        self.notebook_filepath = None
        self.notebook_changed = False
        
        if cmd in {'add', 'add2'}:
            self.notebook_may_change = True
        else:
            self.notebook_may_change = False

        
def read_notebooks(notes_folder_location):
    """Read .ipynb files from specified location.
    
    Params:
        notes_folder_location (str): folder with .ipynb notes
    
    Returns:
        dict str->nbformat.notebooknode.NotebookNode:
            dict mapping .ipynb file paths to notebook objects
    """
    
    # Find all .ipynb files in notes_folder
    pattern = os.path.join(notes_folder_location, '**', '*.ipynb')
    notebook_filepaths = glob.glob(pattern, recursive=True)
    # display(notebook_filepaths)
    # ['/../notes/DeepRL_Notes.ipynb', '/../notes/Coursera_DLAI.ipynb']
    
    file_nb_dict = {}
    
    for file_location in notebook_filepaths:
        with open(file_location, 'r') as f:
            nb = nbformat.read(f, as_version=4)
            file_nb_dict[file_location] = nb
            
    return file_nb_dict

        
def _figure_out_command(meta, head, body, note_ids):
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
        # This note has empty <!------>, meaning it was just added in Jupyter
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
                cmd = Command('noop', id_, head, body)
    return cmd




def commands_prepare(file_nb_dict, anki_deck_name, dbg_print=False):
    """Query Anki DB and check notes folder and prepare commands to sync.
    
    This function does not alter Anki database or notes folder.
    
    Params:
        file_nb_dict (dict str->nbformat.notebooknode.NotebookNode):
            dict mapping .ipynb file paths to notebook objects
        anki_deck_name (str): deck name in Anki database to sync to
        dbg_print (bool): if True, print debug info
        
    Returns:
        list-of-mbrain.Command: list of commands, which if executed, will do sync
            to execute commands pass them to commands_execute() function
    """
    assert isinstance(file_nb_dict, dict)
    assert isinstance(anki_deck_name, str)
    assert isinstance(dbg_print, bool)
    
    existing_note_ids = anki_find_notes(anki_deck_name)
    # print(existing_note_ids)
    # ['1560133178581', '1560133182006', ... ]
    assert len(existing_note_ids) == len(set(existing_note_ids))

    commands = []

    for filename, nb in file_nb_dict.items():
        if dbg_print: print('Processing:', filename)
        for cell in nb['cells']:
            if not is_flashcard(cell):
                continue

            meta, head, body, attachments = process_cell(cell, dbg_print)
            cmd = _figure_out_command(meta, head, body, existing_note_ids)
            if cmd is not None:
                cmd.deck = anki_deck_name
                cmd.cell = cell
                cmd.attachments = attachments
                cmd.notebook_filepath = filename
                commands.append(cmd)
    
    orphaned_ids = set(existing_note_ids)
    for cmd in commands:
        if cmd.id is not None:   # add, add2
            orphaned_ids.remove(cmd.id)
                
    return commands, orphaned_ids


def _exec_command(cmd):
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
        if cmd.cell.source != new_meta:
            # need to update jupyter notebook
            cmd.cell.source = new_meta
            cmd.notebook_changed = True
        for name, (key, value) in cmd.attachments.items():
            if anki_get_media(key) is None:
                anki_add_or_replace_media(key, value)
    elif cmd.cmd == 'update':
        anki_update_note(cmd.id, cmd.head, cmd.body)
    elif cmd.cmd == 'noop':
        pass # do nothing
    else:
        raise ValueError(f'Unknown command: {cmd.cmd}')
        
def commands_execute(file_nb_dict, commands):
    """This will execute given commands
    
    Params:
        commands (list-of-mbrain.Command)
    """
    for cmd in commands:
        print('Executing:', cmd.cmd, cmd.head)
        _exec_command(cmd)
        
    changed_files = {cmd.notebook_filepath for cmd in commands if cmd.notebook_changed}
        
    for fl, nb in file_nb_dict.items():
        if fl in changed_files:
            print('Writing:', fl)
            with open(fl, 'w') as f:
                nbformat.write(nb, f)
