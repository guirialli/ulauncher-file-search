import subprocess
import os
from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action import RenderResultListAction, RunScriptAction

class SearchService:
    def find(self, search: str, path: str='~', extra=''):
        cmd = f"timeout 0.3s bash -c 'cd {path} && fd -a {extra} {search}'"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return [i for i in result.stdout.splitlines() if i and not i.startswith('fd:')]

    def get_item(self, path, name=None, desc='', icon='images/icon.png'):
        return ExtensionResultItem(icon=icon,
                                   name=f'{name if name else path}',
                                   description=desc,
                                   on_enter=RunScriptAction(f'xdg-open "{path}"', []))


class KeywordQueryEventListener(EventListener):

    def on_event(self, event, extension):
        data = event.get_argument()
        keyword = event.get_keyword()
        service = SearchService() 

        fd_keyword = extension.preferences.get('fd')
        fdir_keyword = extension.preferences.get('fdir')
        search_path = extension.preferences.get('dir')
        
        try:
            cut_off = int(extension.preferences.get('cut'))
        except ValueError:
            cut_off = 10 
            
        show_dirs = extension.preferences.get('show_dirs').lower().strip() == 'yes'

        found = []
        if fd_keyword == keyword:
            found = service.find(data, path=search_path)
        elif fdir_keyword == keyword:
            found = service.find(data, path=search_path, extra='-t d')
            
        items = []
        
        for path in found:
            if len(items) >= cut_off:
                break
                
            file_name = os.path.basename(path.rstrip('/'))
            items.append(service.get_item(path, name=file_name, desc=f'Abrir: {path}'))

            if show_dirs and not path.endswith('/'):
                if len(items) >= cut_off:
                    break
                    
                new_path = os.path.dirname(path) + '/'
                dir_name = os.path.basename(new_path.rstrip('/'))
                
                items.append(
                    service.get_item(new_path, 
                                     name=f'↑Dir: {dir_name}', 
                                     desc=f'Diretório do arquivo: {new_path}',
                                     icon='images/folder.png') # Usando ícone de pasta
                )
                
        return RenderResultListAction(items)


class FileSearchExtension(Extension):

    def __init__(self):
        super().__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())
        
if __name__ == '__main__':
    FileSearchExtension().run()