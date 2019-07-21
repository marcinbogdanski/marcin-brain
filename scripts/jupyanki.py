#!/usr/bin/env python3

import os
import sys
import argparse

import mbrain as mb

def sync(notes_folder_location, anki_deck_name, debug=False):
    
    file_nb_dict = mb.read_notebooks(notes_folder_location)
    
    commands = mb.commands_prepare(file_nb_dict, anki_deck_name, dbg_print=debug)
    
    if len(commands) == 0:
        print('Jupyter notes and Anki DB are in sync.')
    else:
        print('Following commands required to sync:')
        for c in commands:
            print(' * ' + c.cmd + ': ' + c.head)
            
        files_to_update = {cmd.notebook_filepath for cmd in commands if cmd.notebook_may_change}
        print('Files that will be potentially updated:')
        for f in files_to_update:
            print(' + ' + f)
    
        do_exec = input('Execute commands? [y/N]:')
        
        if do_exec == 'y':
            print('Executing...')
            mb.commands_execute(file_nb_dict, commands)
        else:
            print('Aborted, nothing was done.')
    
def main():
        
    parser = argparse.ArgumentParser(description='Jupyter <-> Anki sync tool.')
    parser.add_argument('command', choices=['sync', 'prune'], 
                        help='Command to run.')
    parser.add_argument('path', nargs='?',
                        help='Path to folder with .ipynb files, or single file')
    parser.add_argument('deck', nargs='?',
                        help='Name of existing Anki deck to sync with')
    parser.add_argument('--debug', action='store_true',
                        help='Print debug info')
    args = parser.parse_args()
    
    print(args.debug)
    
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
        sync(args.path, args.deck, args.debug)
        



    pass
    
if __name__ == '__main__':
    main()
    
    
    
    