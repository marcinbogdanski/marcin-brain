import json
import urllib


def anki_invoke(action, **params):
    """Exec AnkiConnect RESTful querry.
    
    This method is low level REST API invocation, recommended to use wrappers instead
    
    AnkiConnect documentation:
     - website: https://foosoft.net/projects/anki-connect/
     - github: https://github.com/FooSoft/anki-connect
    
    To install AnkiConnect plugin:
     0. Have Anki already installed and working, account created etc.
     1. Open the Install Add-on dialog by selecting Tools | Add-ons | Browse & Install in Anki.
     2. Input **2055492159** into the text box labeled Code and press the OK button to proceed.
     3. Restart Anki when prompted to do so in order to complete the installation of AnkiConnect.
    
    Params:
        action (str): method to invoke on server, e.g. 'findNotes'
        params (dict): method params, see AnkiConnect documentation
    
    Returns:
        ???: depends on method, see AnkiConnect documentation
    """
    assert isinstance(action, str)
    
    def build_dict(action, **params):
        return {'action': action, 'params': params, 'version': 6}
    
    url = 'http://localhost:8765'
    payload_dict = build_dict(action, **params)
    payload_json = json.dumps(payload_dict).encode('utf-8')
    request = urllib.request.Request(url, payload_json)
    
    with urllib.request.urlopen(request) as f:
        response = json.load(f)
    
    if len(response) != 2:
        raise Exception('response has an unexpected number of fields')
    if 'error' not in response:
        raise Exception('response is missing required error field')
    if 'result' not in response:
        raise Exception('response is missing required result field')
    if response['error'] is not None:
        raise Exception(response['error'])
    return response['result']


def anki_test_db():
    """Make sure 'Basic' model exists and has fields 'Front' and 'Back'."""
    models_list = anki_invoke('modelNames')
    if 'Basic' not in models_list:
        raise ValueError('Could not find "Basic" model in Anki database.')
    
    basic_fileds = anki_invoke('modelFieldNames', modelName='Basic')
    if basic_fileds != ['Front', 'Back']:
        raise ValueError('Model "Basic" fields must be "Front" and "Back"')

        
def anki_get_decks():
    """Get decks in anki database.
    
    Returns:
        list-of-str: list of deck names, e.g. ['Default']
    """
    return anki_invoke('deckNames')


def anki_find_notes(deck):
    """Get all note IDs from specified deck.
    
    Params:
        deck (str): deck name in Anki db
    
    Returns:
        list-of-str: note IDs from that deck
    """
    assert isinstance(deck, str)
    
    decks_list = anki_get_decks()
    
    if deck not in decks_list:
        raise ValueError('Select dect that already exists.')
    
    id_list = anki_invoke('findNotes', query=f'deck:"{deck}"')
    return [str(id_) for id_ in id_list]


def anki_add_note(deck, front, back):
    """Add new note to the Anki database.
    
    Front content must be unique across deck (database?)
    
    TODO: support tags and media files
    
    Params:
        deck (str): name of deck to add note to, must exist
        front (str): note front side: question to display to user
        back (str): note back side: answer expected from user
    
    Returns:
        str: new note ID as string
    """
    assert isinstance(deck, str)
    assert isinstance(front, str)
    assert isinstance(back, str)
    
    decks_list = anki_invoke('deckNames')
    if deck not in decks_list:
        raise ValueError('Select dect that already exists.')
    
    note = {
        'deckName': deck,
        'modelName': 'Basic',
        'fields': { 'Front': front, 'Back': back },
        'options': { 'allowDuplicate': False },
        'tags': [],
    }
    
    id_ = anki_invoke('addNote', note=note)
    
    return str(id_)


def anki_get_note(id_):
    """Get note front and back fields.
    
    TODO: support tags and media
    
    Params:
        id_ (str or int): note ID in Anki database
    
    Returns:
        front (str): note front side (question)
        back (str): note back side (answer)
    """
    assert isinstance(id_, (str, int))  # either works
    
    info_list = anki_invoke('notesInfo', notes=[id_])
    assert len(info_list) == 1
    
    info = info_list[0]
    assert info['modelName'] == 'Basic'
    
    fields = info['fields']
    front = fields['Front']['value']
    back = fields['Back']['value']
    
    return front, back


def anki_update_note(id_, front, back):
    """Update existing note. Note must exist.
    
    Params:
        id_ (str or int): note ID in Anki database
        front (str): note front side: question to display to user
        back (str): note back side: answer expected from user
    """
    assert isinstance(id_, (str, int))  # either works
    assert isinstance(front, str)
    assert isinstance(back, str)
    
    note = {
        'id': id_,
        'fields': { 'Front': front, 'Back': back },
    }
    
    anki_invoke('updateNoteFields', note=note)


def anki_delete_note(id_):
    """Delete node from Anki database.
    
    Params:
        id_ (str or int): note ID in Anki database
    """
    assert isinstance(id_, (str, int))  # either works
    
    anki_invoke('deleteNotes', notes=[id_])