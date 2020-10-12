import PySimpleGUI as sg
import re
"""
    Demo - 2 simultaneous windows using read_all_window
    Both windows are immediately visible.  Each window updates the other.
    
    There's an added capability to "re-open" window 2 should it be closed.  This is done by simply calling the make_win2 function
    again when the button is pressed in window 1.
    
    The program exits when both windows have been closed
        
    Copyright 2020 PySimpleGUI.org
"""
def LEDIndicator(key=None, radius=30):
    return sg.Graph(canvas_size=(radius, radius),
             graph_bottom_left=(-radius, -radius),
             graph_top_right=(radius, radius),
             pad=(0, 0), key=key, enable_events=True)


def from_rgb(rgb):
    """translates an rgb tuple of int to a tkinter friendly color code
    """
    return '#' + ''.join('%02x'%i for i in rgb) 

class Gui:
    def __init__(self, pick_by_light):
        self._pbl = pick_by_light
        self.window_main = self.make_win_main()
        self.window_virtual = self.make_win_virtual()

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
      
        layout.append([sg.Button('Close',key='Exit')])

        return sg.Window('Window Title2', layout, finalize=True)

    def make_win_main(self):
        layout = [[sg.Text('Window 1')],
                [sg.Text('Enter something to output to Window 2')],
                [sg.Input(key='-IN-', enable_events=True)],
                [sg.Text(size=(25,1), key='-OUTPUT-')],
                [sg.Button(button_text='Open Virtual\nPick By Light', key='OpenVirtual')],
                [sg.Button('Exit')]]
        return sg.Window('Window Title', layout, finalize=True)

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

    def run(self):

        self.window_virtual.move(self.window_main.current_location()[0], self.window_main.current_location()[1]+220)

        while True:             # Event Loop
            window, event, values = sg.read_all_windows(timeout=100)
            if event == sg.WIN_CLOSED or event == 'Exit':
                print("event win closed")
                window.close()
                if window == self.window_virtual:       # if closing win 2, mark as closed
                    self.window_virtual = None
                elif window == self.window_main:     # if closing win 1, mark as closed
                    self._pbl.deselect_all()
                    
                    break

            elif event == 'OpenVirtual':
                if not self.window_virtual:
                    self.window_virtual = self.make_win_virtual()
                    self.window_virtual.move(self.window_main.current_location()[0], self.window_main.current_location()[1] + 220)

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
        

