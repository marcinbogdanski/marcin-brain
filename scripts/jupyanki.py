import os
import sys
import argparse

module_path = os.path.abspath(os.path.join('..'))
if module_path not in sys.path:
    sys.path.append(module_path)

import mbrain as mb

def dry_run(notes_folder_location, anki_deck_name):
#     notes_folder_location = '/home/marcin/marcin-notes'
#     anki_deck_name = 'Notes'
    
    file_nb_dict = mb.read_notebooks(notes_folder_location)
    
    commands = mb.commands_prepare(file_nb_dict, anki_deck_name)
    
    if len(commands) == 0:
        print('Jupyter notes and Anki DB are in sync.')
    else:
        print('Following commands required to sync:')
        for c in commands:
            print(c.cmd + ': ' + c.head)
    
def main():
        
    parser = argparse.ArgumentParser(description='Jupyter <-> Anki sync tool.')
    parser.add_argument('command', choices=['sync', 'prune'], 
                        help='Command to run.')
    parser.add_argument('path', nargs='?',
                        help='Path to folder with .ipynb files, or single file')
    parser.add_argument('deck', nargs='?')
    args = parser.parse_args()
    
    print('Command:', args.command)
    print('Path:   ', args.path)
    print('Deck:   ', args.deck)
    
    if args.command == 'sync':
        if args.path is None:
            parser.error('Please specify path.')
        if not os.path.exists(args.path):
            parser.error('Specified path must exist.')
        if args.deck is None:
            parser.error('Please specify Anki deck.')
        dry_run(args.path, args.deck)
        



    pass
    
if __name__ == '__main__':
    main()
    
    
    
    