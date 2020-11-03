import PySimpleGUI as sg
import re
import os
"""
    Gui for pick by light 
"""

import logging  
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def LEDIndicator(key=None, radius=30):
    return sg.Graph(canvas_size=(radius, radius),
             graph_bottom_left=(-radius, -radius),
             graph_top_right=(radius, radius),
             pad=(0, 0), key=key, enable_events=True)


def from_rgb(rgb):
    """translates an rgb tuple of int to a tkinter friendly color code
    """
    return '#' + ''.join('%02x'%i for i in rgb) 


default_image = 'img/default-placeholder.png'
def check_image(path):
    if not os.path.isfile(path):
        return default_image
    return path    

class Gui:
    def __init__(self, pick_by_light, default_content_map_path = None):
        self._pbl = pick_by_light
        self.window_main = self.make_win_main()
        self.window_main.maximize()
        
        self.window_virtual = None
        self.window_work = None
        sg.theme('Dark Blue 3')  # please make your windows colorful

    def make_win_virtual(self):
        layout = [[sg.Text('Window 2')],
                  [sg.Text('Select, Port, Activity, Light')]
                 ]
        for port_number, port in self._pbl.get_ports():
            row = [sg.Check(text = None, key='_C{}_'.format(port_number), enable_events=True),
                sg.Text('Port {}'.format(port_number)), 
                LEDIndicator('_A{}_'.format(port_number)), 
                LEDIndicator('_LED{}_'.format(port_number)),
                ]
            layout.append(row)
      
        layout.append([sg.Button('Close',key='EXIT')])

        return sg.Window('Window Title2', layout, finalize=True)

    def make_win_main(self):
        
        content_strings = [' {}: {}'.format(port, value) for port, value in self._pbl.get_all_contents_display_name().items()]

        content = [[sg.Text('Content', font=('Helvetica', 20))],
                   [sg.Listbox(values=content_strings, size=(30,8), no_scrollbar=True, key='CONTENTMAPLISTBOX', enable_events=True)],
                   [sg.Button('Change/Update item', key='CHANGECONTENTITEM')],
                   [sg.Button('Load content map', key='LOADCONTENTMAP')],
                   [sg.Button('Save content map', key='SAVECONTENTMAP')]]

        layout = [[sg.Text('Smart Manual Station Pick by light', justification='center', size=(50,1),font=('Helvetica', 20))],
                  [sg.Text('Waiting for commands', justification='center', size=(50,1), font=('Helvetica', 20))],
                [sg.Image('img/AAU_LOGO_WHITE_UK.png'),sg.Column(content)],
                [sg.Button(button_text='Open Virtual\nPick By Light', key='OPENVIRTUAL'),
                    sg.Button(button_text='test work window', key='TESTWORKWINDOW'),
                    sg.Button('Exit', key = 'EXIT')
                ],
        ]
        return sg.Window('Window Title', layout, finalize=True)


    def make_win_work(self, port_number, instructions):
        text_instructions = 'Instructions: {}'.format(instructions)
        content = self._pbl.get_content(port_number)
        image = check_image(content.get('image_path',''))

        col = [[sg.Text('Box content name {}'.format(content.get('display_name','')), font=('Helvetica', 20) ), 
                  sg.Button(button_text='content description', key='ShowContentDescription', image_filename='img/info-circle-solid.png',tooltip='content description', size=(0,0),image_subsample=15, border_width=0, pad=(0,0))],
               [sg.Multiline(text_instructions, size=(50,10),font=('Helvetica', 20))]    
              ]

        layout = [[sg.Column(col),sg.Image(image,size=(500,500))],
                  [sg.Submit(size=(10,5), font=('Helvetica', 20), key='SUBMIT'), sg.Cancel(size=(10,5),font=('Helvetica', 20), key='CANCELWORK')]]

        return sg.Window('smart manual station', layout, finalize=True)

    def make_win_change_content(self, port_number):
        content = self._pbl.get_content(port_number)
        layout = []
        layout.append([sg.Text('Please update the fields to your needs')])
        for key, value in content.items():
            layout.append([sg.Text(key, size=(15, 1)), sg.InputText(default_text=value,key=key)])

        layout.append([sg.Submit(), sg.Cancel()])
        return sg.Window('Content data entry', layout, finalize=True, modal=True)

    def _set_virtual_led(self, window, key, color):
        """Sets the LED indicator"""
        graph = window[key]
        graph.erase()
        if type(color) in [tuple,list]: color = from_rgb(color)
        graph.draw_circle((0, 0), 12, fill_color=color, line_color=color)

    def _set_checkbox(self, window, key, value):
        """Updates the value of the checkbox"""
        check = window[key]
        check.Update(value=value)

    def _update_content_listbox(self):
        content_strings = [' {}: {}'.format(port, value) for port, value in self._pbl.get_all_contents_display_name().items()]
        listbox = self.window_main.find_element('CONTENTMAPLISTBOX')
        listbox.Update(values=content_strings)

    def run(self):


        while True:             # Event Loop
            window, event, values = sg.read_all_windows(timeout=100)

            if event != '__TIMEOUT__':
                logger.debug(window, event, values)

            if event == sg.WIN_CLOSED or event in ['EXIT','SUBMIT']:
                print("event win closed")
                window.close()
                if window == self.window_virtual:       # if closing win 2, mark as closed
                    self.window_virtual = None
                elif window == self.window_work:
                    self.window_work = None
                elif window == self.window_main:     # if closing win 1, mark as closed
                    self._pbl.deselect_all()
                    
                    break

            elif event == 'OPENVIRTUAL':
                if not self.window_virtual:
                    self.window_virtual = self.make_win_virtual()
                    self.window_virtual.move(self.window_main.current_location()[0], self.window_main.current_location()[1] + 220)
            
            elif event == 'TESTWORKWINDOW':
                if not self.window_work:
                    self.window_work = self.make_win_work(2,'test instructions')
                    self.window_work.maximize()

            elif event == 'LOADCONTENTMAP':
                event, values = sg.Window('load content map', [[sg.Text('Filename')], [sg.Input(), sg.FileBrowse(initial_folder='./',file_types=(('yaml','*.yaml')))], [sg.OK(), sg.Cancel()] ]).read(close=True)
                if event == 'OK':
                    try:
                        self._pbl.load_content_map(values['Browse'])
                        self._update_content_listbox()
                    except Exception as e:
                        sg.Popup('error, could not load content map. Error = {}'.format(e))

            elif event == 'CHANGECONTENTITEM':
                try:    
                    port_number = int(re.search('[0-9]+', values['CONTENTMAPLISTBOX'][0]).group())
                    window = self.make_win_change_content(port_number)
                    event, values = window.read()
                    print(event, values)
                    window.close()
                    if event == 'Submit':
                        self._pbl.change_content_item(port_number,values)
                        self._update_content_listbox()
                except IndexError:
                    logger.info('an item must be selected from the listbox')

            elif event == 'SAVECONTENTMAP':
                event, values = sg.Window('Save content map', [[sg.Text('Path/Filename')], [sg.Input(key='INPUT'), sg.FileSaveAs('Browse', initial_folder='./',file_types=(('yaml','.yaml'),))], [sg.OK(), sg.Cancel()] ]).read(close=True)
                if event == 'OK':
                    try:
                        print(event,values)
                        self._pbl.save_content_map(values['INPUT'])
                    except Exception as e:
                        sg.Popup('error, could not load content map. Error = {}'.format(e))
                    
            elif event == 'ShowContentDescription':
                logger.debug('yaay content description pop not implemented yet.')

            elif '_A' in event and self.window_virtual is not None:
                result = re.findall(r'\d+',event)
                port_number = int(result[0])
                tmp_port = self._pbl.get_port(port_number)
                if tmp_port is not None:
                    tmp_port.make_activity()
            
            elif '_C' in event and self.window_virtual is not None:
                result = re.findall(r'\d+',event)
                port_number = int(result[0])
                if values[event]:
                    self._pbl.select_port(port_number)
                else:
                    self._pbl.deselect_port(port_number) 
            
            elif self.window_virtual is not None: # update the values 
                for port_number, port in self._pbl.get_ports():
                    self._set_virtual_led(self.window_virtual, '_A{}_'.format(port_number), 'green' if port.activity else 'cyan')
                    light = [int(i * port.get_light() / 100) for i in [255,255,255]]
                    self._set_virtual_led(self.window_virtual, '_LED{}_'.format(port_number), light )
                    self._set_checkbox(self.window_virtual, '_C{}_'.format(port_number), self._pbl.get_port_state(port_number).selected)
        
