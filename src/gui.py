import PySimpleGUI as sg
import re
import os
from PIL import Image, ImageTk
import io
"""
    Gui for pick by light 
"""

import logging  
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)



def LEDIndicator(key=None, radius=30):
    """Returns a simplegui graph element that imitates a round indicator light.

    Args:
        key (str, optional): String key to access the graph element. Defaults to None.
        radius (int, optional): size of the created led indicator. Defaults to 30.

    Returns:
        sh.Graph: PySimpleGui graph element
    """
    return sg.Graph(canvas_size=(radius*2, radius*2),
             graph_bottom_left=(-radius, -radius),
             graph_top_right=(radius, radius),
             key=key, enable_events=True)


def from_rgb(rgb):
    """Translates an rgb tuple of three int to a tkinter friendly color code

    Args:
        rgb tuple(int,int,int): red green blue values respectively

    Returns:
        str: hex string for color value
    """

    return '#' + ''.join('%02x'%i for i in rgb) 


default_image = 'img/default-placeholder.png'
def check_image(path):
    """checks if the giver path points to a file and if not 
    it returns a default dummy image instead.
    
    Args:
        path (string): pathstring. Can be relative or absolute
    Returns:
        string: path to the image that shall be displayed. 
    """
    if not os.path.isfile(path):
        return default_image
    return path    

def get_img_data(image_path, maxsize=(500, 500)):
    """Generate image data using PIL
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    image_apspath = os.path.join(script_dir, image_path)
    img = Image.open(image_apspath)
    img.thumbnail(maxsize)
    bio = io.BytesIO()
    img.save(bio, format="PNG")
    del img
    return bio.getvalue()
# ------------------------------------------------------------------------------

class Gui:
    """Smart Manual Station Graphical User Interface
       
    """
    def __init__(self, pick_by_light, default_content_map_path = None):
        self._pbl = pick_by_light
        self.window_main = self.make_win_main()
        self.window_main.move(0,0)
        self.windows_work = {port_number:None for port_number, port in self._pbl.get_ports()}
        self.window_virtual = None

        self.screen_bump = False

        sg.theme('Dark Blue 3')  # please make your windows colorful

    def make_win_virtual(self):
        layout = [[sg.Text('Select, Port, Activity, Light')],
                  [sg.Text('Select with the chek boxes and make\nactivity by pressing the blue dots.')]
                 ]
        for port_number, port in self._pbl.get_ports():
            row = [sg.Check(text = None, key='_C{}_'.format(port_number), enable_events=True, size=(2,1), auto_size_text=True,),
                   sg.Text('Port {}'.format(port_number), size=(10,1), font=('Helvetica', 14),justification='left'), 
                   LEDIndicator('_A{}_'.format(port_number),radius=10), 
                   LEDIndicator('_LED{}_'.format(port_number),radius=10),
                ]
            layout.append(row)
      
        layout.append([sg.Button('Close',key='EXITVIRTUAL')])

        return sg.Window('Virtual', layout, finalize=True, keep_on_top=True)

    def make_win_main(self):
        content_strings = [' {}: {}'.format(port, value) for port, value in self._pbl.get_all_contents_display_name().items()]
        
        content = [[sg.Text('Content', font=('Helvetica', 14))],
                   [sg.Listbox(values=content_strings, size=(30,8), no_scrollbar=True, key='CONTENTMAPLISTBOX', enable_events=True,font=('Helvetica', 14))],
                   [sg.Button('Change/Update item', key='CHANGECONTENTITEM',size=(30,1), font=('Helvetica', 14))],
                   [sg.Button('Load content map', key='LOADCONTENTMAP',size=(30,1), font=('Helvetica', 14))],
                   [sg.Button('Save content map', key='SAVECONTENTMAP',size=(30,1), font=('Helvetica', 14))]]

        image_aau_logo = get_img_data('img/aau-logo-white-uk.png',(300,300))
        welcome_col=[[sg.Text('Smart Manual Station Pick by light', justification='center', size=(40,1),font=('Helvetica', 14))],
                  [sg.Text('Waiting for commands', justification='center', size=(40,1), font=('Helvetica', 14))],
                  [sg.Image(data=image_aau_logo)]]


        layout = [[sg.Column(welcome_col), sg.Column(content)],
                  [sg.HorizontalSeparator(pad=(0,20))],
                  [
                      sg.Button(button_text='Open Virtual Pick By Light', key='OPENVIRTUAL', size=(25,1),font=('Helvetica', 14)),
                      sg.Button('Exit', key = 'EXIT',size=(25,1),font=('Helvetica', 14))
                  ]
                 ]
        return sg.Window('AAU SMART MANUAL STATION', layout, finalize=True ,size=(800,480), keep_on_top=False)

    def make_win_work(self, port_number, instructions):
        text_instructions = 'Instructions: {}'.format(instructions)
        content = self._pbl.get_content(port_number)
        image_path = check_image(content.get('image_path',''))
        content_image = get_img_data(image_path, maxsize= (250,250))
        description = content.get('description','')
        info_icon = get_img_data('./img/info-circle-solid.png',maxsize=(18,18))

        col = [[sg.Text('Port{} Content: {}'.format(port_number, content.get('display_name','')), font=('Helvetica', 14) ), 
                  sg.Image(data=info_icon,key='SHOWCONTENTDESCRIPTION',enable_events=True)],
               [sg.Multiline(text_instructions,disabled = True, size=(40,8),font=('Helvetica', 14))]    
              ]

        layout = [[sg.Column(col),sg.Image(data=content_image)],
                  [sg.Submit(size=(10,5), font=('Helvetica', 14), key='SUBMITWORK',metadata=port_number)]]

        return sg.Window('PORT {} WORK WINDOW'.format(port_number), layout, finalize=True, keep_on_top=True, metadata=port_number)

    def make_win_change_content(self, port_number):
        content = self._pbl.get_content(port_number)
        layout = []
        layout.append([sg.Text('Please update the fields to your needs')])
        for key, value in content.items():
            layout.append([sg.Text(key, size=(15, 1)), sg.InputText(default_text=value,key=key)])

        layout.append([sg.Submit(), sg.Cancel()])
        return sg.Window('Content data entry', layout, finalize=True, modal=True)

    def _set_virtual_led(self, window, key, color):
        """Used to sets the LED indicator on the vritual pick by light window"""
        graph = window[key]
        graph.erase()
        if type(color) in [tuple,list]: color = from_rgb(color)
        graph.draw_circle((0, 0), 8, fill_color=color, line_color=color)

    def _set_checkbox(self, window, key, value):
        """Updates the value of the checkbox on the virtual pick by light window"""
        check = window[key]
        check.Update(value=value)

    def _update_content_listbox(self):
        """Updates the content list on the main window"""
        content_strings = [' {}: {}'.format(port, value) for port, value in self._pbl.get_all_contents_display_name().items()]
        listbox = self.window_main.find_element('CONTENTMAPLISTBOX')
        listbox.Update(values=content_strings)

    def run(self):
        """Blocking call that runs the GUI until it exits. 
        """
        while True:             # Event Loop
            window, event, values = sg.read_all_windows(timeout=100)

            if event != '__TIMEOUT__':
                logger.debug(window, event, values)

            if event == sg.WIN_CLOSED or event in ['EXIT', 'EXITVIRTUAL']:
                logger.info("event win closed")
                window.close()
                if window == self.window_virtual:       # if closing win 2, mark as closed
                    self.window_virtual = None
                elif window == self.window_main:     # if closing win 1, mark as closed
                    self._pbl.deselect_all()
                    break

            elif event == 'OPENVIRTUAL':
                if not self.window_virtual:
                    self.window_virtual = self.make_win_virtual()
                    self.window_virtual.move(self.window_main.current_location()[0], self.window_main.current_location()[1] + 100)
            
            elif event == 'SUBMITWORK':
                port_number = window['SUBMITWORK'].metadata
                self._pbl.deselect_port(port_number)
                window.close()
                self.windows_work[port_number] = None

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
                    window.close()
                    if event == 'Submit':
                        self._pbl.set_content(port_number,values)
                        self._update_content_listbox()
                except IndexError:
                    logger.info('an item must be selected from the listbox')

            elif event == 'SAVECONTENTMAP':
                event, values = sg.Window('Save content map', [[sg.Text('Path/Filename')], [sg.Input(key='INPUT'), sg.FileSaveAs('Browse', initial_folder='./',file_types=(('yaml','.yaml'),))], [sg.OK(), sg.Cancel()] ]).read(close=True)
                if event == 'OK':
                    try:
                        self._pbl.save_content_map(values['INPUT'])
                    except Exception as e:
                        sg.Popup('error, could not load content map. Error = {}'.format(e))
                    
            elif event == 'SHOWCONTENTDESCRIPTION':
                content = self._pbl.get_content(port_number)
                description = content.get('description','')
                sg.popup(description, keep_on_top=True)
                

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
                    self.windows_work[port_number] = None
            
            ###### update the virtual pick by light window if it is open
            if self.window_virtual is not None: # update the values 
                for port_number, port in self._pbl.get_ports():
                    self._set_virtual_led(self.window_virtual, '_A{}_'.format(port_number), 'green' if port.activity else 'cyan')
                    light = [int(i * port.get_light() / 100) for i in [255,255,255]]
                    self._set_virtual_led(self.window_virtual, '_LED{}_'.format(port_number), light )
                    self._set_checkbox(self.window_virtual, '_C{}_'.format(port_number), self._pbl.get_port_state(port_number).selected)
        
            ###### Check if something is selected, open the work window
            ports_state = self._pbl.get_ports_state()
            for port_number, state in ports_state.items():
                if state.selected and self.windows_work[port_number] is None:
                    self.windows_work[port_number] = self.make_win_work(port_number,state.select_instructions)
                    self.windows_work[port_number]


            ##### make sure the screen is turned on when there is activity
            for port_number, port in self._pbl.get_ports():
                if port.activity or port.get_light():
                    os.system("sudo xset s reset")
