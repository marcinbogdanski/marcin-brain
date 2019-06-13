

import mbrain as mb
import nbformat

def dry_run():
    notes_folder_location = '/home/marcin/marcin-notes'
    anki_deck_name = 'Notes'
    
    file_nb_dict = mb.read_notebooks(notes_folder_location)
    
    commands = mb.commands_prepare(file_nb_dict, anki_deck_name)
    
    for c in commands:
        print(c.cmd + ': ' + c.head)
    
def main():
    
    pass
    
if __name__ == '__main__':
    main()
    
    
    
    