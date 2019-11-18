# author: WutDuk? https://github.com/jcemerson
# date: 2019-11-17
# version: 1.3
# description:
"""
    The Linux version of my original WinShutdown application:

        https://github.com/jcemerson/WinShutdown

    This was strictly designed to meet the requirements my wife defined
    for her needs, namely:

        1. Simple, easy-to-use interface
        2. Large buttons for convenient selection
        3. Preset time-settings for convenient, quick setting of timer
        4. Large, easy-to-see UI and timer

    We literally use this tool every night to shutdown our bedroom PC,
    which is strictly used to watch TV in bed, after we fall asleep.

    As such, this app's current functionality is limited in scope and
    is likely to not be all things everybody ever wanted in such a
    tool, nor anything else it was never meant to be.

    That said, I do intend to add enhacements with time to offer
    increased flexibility and options for different use-cases. Feel
    free to suggest features and/or functionality you wish to see,
    or fork the repository and submit your own pull requests..

    Also, please feel free to help me grow and perfect this craft by
    offering constructive criticism and guidance toward improving the
    existing codebase.
"""

# import sys
import os
import json
import ast
import kivy
from kivy import Config
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.behaviors import ToggleButtonBehavior
from kivy.uix.popup import Popup
from kivy.animation import Animation
from kivy.properties import StringProperty, NumericProperty, \
    BooleanProperty, ListProperty
from kivy.clock import Clock
# import tray as systray


# Supported Kivy version required for operation. Older version may work too,
# but they're not supported. You can remove or modify this setting at your own
# risk.
kivy.require('1.10.1')

# Set config.ini setting for this instance of the app only
# (as opposed to writing to the file which would impact ALL Kivy apps)
Config.set(
    'graphics',
    'fullscreen',
    0,
)
Config.set(
    'graphics',
    'resizable',
    0,
)
Config.set(
    'kivy',
    'exit_on_escape',
    0,
)
Config.set(
    'kivy',
    'window_icon',
    './Images/power-on-white.png',
)


# Import Window for Keybindings functionality -- When placed before config,
# Kivy would flicker during loading. Relocated lower in the process to ensure
# Window is loaded AFTER initial config is defined
from kivy.core.window import Window
Window.size = (800, 600)
Window.fullscreen = False


# Set the path to the user settings file:
file_path = os.path.dirname(os.path.realpath(__file__))
filename = 'user_settings.json'
user_settings_file = os.path.join(file_path, filename)


class ImminentPopup(Popup):
    """
    A popup presented when the user forces the countdown to 00:00:00.

    The user will be warned that they are about to force the selected
    command to be executed and asked to confirm this action by
    selecting a button: Yes or No.
    """
    label_text = StringProperty('')

    def __init__(self, cmd):
        super(ImminentPopup, self).__init__()
        self.title = f'Imminent {cmd}!'
        self.label_text = (
        'By forcing an active countdown to 00:00:00 you are about to '
        f'initiate an [i][b]imminent {cmd}[/b][/i].\n\n'
        'Do you wish to continue?'
        )


class FinalPopup(Popup):
    """
    A popup presented at the end of the countdown just priot to sending
    the final command and the App auto-closing.

    A message is presented while a countdown of 5 seconds executes. At
    the end, the final command is executed and the App is stopped.

    Note: Future enhancements may make this optional (meaning immediate
    execution of the final command) and/or the final_cmd countdown
    configurable.
    """
    countdown = NumericProperty(5.9)

    def __init__(self):
        super(FinalPopup, self).__init__()

    def start_final_timer(self):
        """
        Starts the countdown to cmd execution and App auto-closing.
        """
        # Cancel any active animation
        Animation.cancel_all(self)
        # Define the Animation; where we're going, where we're coming from.
        self.anim = Animation(countdown=0, duration=self.countdown)
        # Bring minimized and/or hidden window front-and-center.
        App.get_running_app().root._show_app_window()
        # Execute final command.
        self.anim.bind(on_complete=App.get_running_app().root.exec_cmd)
        # Stop the App.
        self.anim.bind(on_complete=App.get_running_app().stop)
        # Close the system tray icon (current only supported in Windows).
        # self.anim.bind(on_complete=App.get_running_app().root.close_systray)
        self.anim.start(self)


class LinShutdownTimer(GridLayout, ToggleButtonBehavior):
    """
    Top-level/root containing the "meat" of the app.
    """
    # Define default layout attributes
    font_size = 20
    widget_padding = (25, 10, 25, 10)
    spacer_width = 10
    abort_disabled = BooleanProperty(True)
    abort_background_color = ListProperty([1, 1, 1, 1])
    popup_active = BooleanProperty(False)
    # Define default cmd button attributes
    shutdown_btn_disabled = BooleanProperty(False)
    shutdown_btn_state = StringProperty('normal')
    restart_btn_disabled = BooleanProperty(False)
    restart_btn_state = StringProperty('normal')
    suspend_btn_disabled = BooleanProperty(False)
    suspend_btn_state = StringProperty('normal')
    logoff_btn_disabled = BooleanProperty(False)
    logoff_btn_state = StringProperty('normal')
    # Define default time button attributes
    set20_disabled = BooleanProperty(False)
    set20_state = StringProperty('normal')
    set40_disabled = BooleanProperty(False)
    set40_state = StringProperty('normal')
    set60_disabled = BooleanProperty(False)
    set60_state = StringProperty('normal')
    set90_disabled = BooleanProperty(False)
    set90_state = StringProperty('normal')
    set120_disabled = BooleanProperty(False)
    set120_state = StringProperty('normal')
    preset_status = BooleanProperty(True)
    preset_keybinding_enabled = BooleanProperty(True)
    # Define -15min/+15min buttons' status
    sub_time_disabled = BooleanProperty(True)
    add_time_disabled = BooleanProperty(False)
    # Establish countdown variable
    countdown = NumericProperty(0)
    # Define Start/Pause button attributes
    start_pause = StringProperty('Start')
    start_pause_disabled = BooleanProperty(True)
    # Establish final cmd string variable
    final_cmd = StringProperty('')


    # Retrieve default settings if the file exists,
    # else create the file and set the defaults.
    try:
        with open(user_settings_file, 'r') as f:
            user_settings = ast.literal_eval(f.read())
    except FileNotFoundError:
        user_settings = {
            'default_cmd': 'shutdown',
            'default_time': 'set20',
        }
        with open(user_settings_file, 'w+') as f:
            json.dump(user_settings, f, indent=4)


    def __init__(self):
        super(LinShutdownTimer, self).__init__()
        # Instantiate Window object
        self._app_window = Window
        # Obtain instance of keyboard and bind key-press event.
        self._keyboard = self._app_window.request_keyboard(
            self._keyboard_closed,
            self,
        )
        self._keyboard.bind(on_key_down=self._on_keyboard_down)


    def apply_defaults(self):
        """
        Applies the default command and time selections based on the
        user_settings dict (i.e., user_settings_file).
        """
        default_cmd = self.user_settings['default_cmd']
        default_time = self.user_settings['default_time']
        # cmd_group buttons
        if default_cmd == 'shutdown':
            self.shutdown_btn_state = 'down'
        elif default_cmd == 'restart':
            self.restart_btn_state = 'down'
        elif default_cmd == 'suspend':
            self.suspend_btn_state = 'down'
        elif default_cmd == 'log off':
            self.logoff_btn_state = 'down'
        # time buttons
        if default_time == 'set20':
            self.set20_state = 'down'
            self.countdown = 20*60
        elif default_time == 'set40':
            self.set40_state = 'down'
            self.countdown = 40*60
        elif default_time == 'set60':
            self.set60_state = 'down'
            self.countdown = 60*60
        elif default_time == 'set90':
            self.set90_state = 'down'
            self.countdown = 90*60
        elif default_time == 'set120':
            self.set120_state = 'down'
            self.countdown = 120*60
        # Enable Start/Pause and -15 min buttons
        self.start_pause_disabled = False
        self.sub_time_disabled = False


    def get_cmd(self):
        """
        Get the current button selection from the cmd_group buttons.
        """
        if self.ids.shutdown.state == 'down':
            self.cmd = 'Shutdown'
        elif self.ids.restart.state == 'down':
            self.cmd = 'Restart'
        elif self.ids.suspend.state == 'down':
            self.cmd = 'Suspend'
        elif self.ids.logoff.state == 'down':
            self.cmd = 'Log Off'
        return self.cmd


    def get_time(self):
        """
        Get the current button selection from the preset_duration buttons.
        """
        if self.ids.set20.state == 'down':
            self.time = 'set20'
        elif self.ids.set40.state == 'down':
            self.time = 'set40'
        elif self.ids.set60.state == 'down':
            self.time = 'set60'
        elif self.ids.set90.state == 'down':
            self.time = 'set90'
        elif self.ids.set120.state == 'down':
            self.time = 'set120'
        return self.time


    def set_app_settings(self):
        """
        Write the current user_settings to user_settings_file.
        """
        with open(user_settings_file, 'w') as f:
            json.dump(self.user_settings, f, indent=4)


    def get_curr_settings(self):
        """
        Retrieve current command and time settings values and
        update user_settings dict.
        """
        self.user_settings['default_cmd'] = self.get_cmd().lower()
        self.user_settings['default_time'] = self.get_time()


    def _keyboard_closed(self):
        """
        Close keyboard instance and reset to None.
        """
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None


    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        """
        Trigger button presses from key-press events.

        Underlined characters in a button's text indicate "hotkeys", or
        keyboard shortcuts, to simulate a gui button press.

            Command Buttons:
            * Shutdown: s
            * Restart: r
            * Suspend: p
            * Log Off: l

            Preset Time Buttons:
            * 20: 2
            * 40: 4
            * 60: 6
            * 90: 9
            * 120: 1

            Misc.:
            * Abort: a

        Some buttons have multiple keyboard shortcuts, such as:

            * Start/Pause: Spacebar; Enter
            * -15 min: Down-arrow (v); left-arrow (<), minus (-)
            * +15 min: Up-arrow (^); right-arrow (>), plus (+)

        See /kivy/core/window/__init__.py for keycode details.
        """
        if self.preset_keybinding_enabled == True:
            # cmd buttons
            if keycode[0] == 115:
                self.ids.shutdown.trigger_action(0)
            elif keycode[0] == 114:
                self.ids.restart.trigger_action(0)
            elif keycode[0] == 112:
                self.ids.suspend.trigger_action(0)
            elif keycode[0] == 108:
                self.ids.logoff.trigger_action(0)
            # preset duration buttons
            elif keycode[0] in (50, 258):
                self.ids.set20.trigger_action(0)
            elif keycode[0] in (52, 260):
                self.ids.set40.trigger_action(0)
            elif keycode[0] in (54, 262):
                self.ids.set60.trigger_action(0)
            elif keycode[0] in (57, 265):
                self.ids.set90.trigger_action(0)
            elif keycode[0] in (49, 257):
                self.ids.set120.trigger_action(0)

        # subtract time / add time buttons
        if self.sub_time_disabled == False:
            if keycode[0] in (45, 269, 274, 276):
                self.ids.minus15.trigger_action(0)

        if self.add_time_disabled == False:
            if keycode[0] in (61, 270, 273, 275):
                self.ids.plus15.trigger_action(0)

        # If there's no active popup, then
        if self.popup_active == False:
            # Start/Stop buttons
            if self.countdown > 0 and self.start_pause_disabled == False:
                if keycode[0] in (13, 16, 32, 271):
                    self.ids.start_pause.trigger_action(0)

            # Abort button
            if  self.abort_disabled == False:
                if keycode[0] == 97:
                    self.ids.abort.trigger_action(0)

        # If there is an active popop, then
        if self.popup_active == True:
            # ImminentPopup Yes/No buttons
            if keycode[0] == 121:
                self.imminent_popup.ids.yes.trigger_action(0)
            elif keycode[0] == 110:
                self.imminent_popup.ids.no.trigger_action(0)


    def toggle_keybinding_allowed(self):
        """
        Enable/Disable keybindings for command and time buttons.
        """
        if self.ids.start_pause.state == 'down':
            self.preset_keybinding_enabled = False
        else:
            self.preset_keybinding_enabled = True


    def initiate_shutdown(self, *args):
        """
        Build the command string to execute and call the Final Popup.
        """
        cmd = self.cmd
        # If the Start/Pause button is down (should say 'Pause') and the countdown is at 0, then
        if self.countdown == 0:
            # If the Shutdown button is down, then
            if cmd == 'Shutdown':
                # Compile the cmd string for a shutdown
                self.final_cmd = 'systemctl poweroff'
            # Else, if the Restart button is down, then
            elif cmd == 'Restart':
                # Compile the cmd string for a restart
                self.final_cmd = 'systemctl reboot'
            # Else, if the Suspend button is down, then
            elif cmd == 'Suspend':
                # Compile the cmd string for suspend
                self.final_cmd = 'systemctl suspend'
            # Else, if the Log Off button is down, then
            elif cmd == 'logoff':
                # Compile the cmd string for log off
                self.final_cmd = 'gnome-session-quit --force'
            # Instantiate and open the final popup then start final countdown
            # to cmd execution (5 seconds)
            self.final_popup = FinalPopup()
            self.final_popup.open()
            self.popup_active = True
            self.final_popup.start_final_timer()


    def _show_app_window(self):
        """
        Bring minimized and/or hidden App window to the forefront.
        """
        self._app_window.show()
        self._app_window.raise_window()


    def exec_cmd(self, *args):
        """
        Send final cmd to command shell.
        """
        os.system(self.final_cmd)


    def set_timer(self, button_time):
        """
        Set the countdown timer.

        Note: This doesn't add time to the countdown.
        Instead it replaces the current countdown with a new time.
        """
        # If the countdown is at 0, then
        if self.countdown == 0:
            # Then set the countdown to the time of the button that
            # initiated the call
            self.countdown = button_time


    def clear_timer(self):
        """
        Clear the timer to 00:00:00.
        """
        self.countdown = 0


    def toggle_sub_time_status(self):
        """
        Enable/Disable the '-15 min' button.
        """
        # If the countdown is less than 15 minutes, then
        if self.countdown < 15 * 60:
            # The '-15 min' button is disabled because there's
            # no time to subtract
            self.sub_time_disabled = True
        # Otherwise, the button is active
        else:
            self.sub_time_disabled = False


    def toggle_add_time_status(self):
        """
        Enable/Disable the '+15 min' button.
        """
        # If '+ 15 min' button is not disabled, set to disabled
        if self.add_time_disabled == False:
            self.add_time_disabled = True
        # Else, if countdown is 0 and '+ 15 min' button is disabled,
        # make it active
        elif self.countdown == 0 or self.add_time_disabled == True:
            self.add_time_disabled = False


    def toggle_start_pause_status(self):
        """
        Enable/Disable the 'Start/Pause' button.
        """
        # If the countdown is greater than 0
        if self.countdown > 0:
            # The Start/Pause button is active and can be clicked
            self.start_pause_disabled = False
        else:
            # Otherwise the timer is at 0 and there's no function for
            # this button, so it's disabled
            self.start_pause_disabled = True


    # Method to toggle the Abort button state
    def toggle_abort_status(self):
        """
        Enable/Disable the 'Abort' button.
        """
        # If countdown is greater than 0 and the Start/Pause button
        # is down, then
        if self.countdown > 0 and self.ids.start_pause.state == 'down':
            # The Abort button is active, and colored red
            self.abort_disabled = False
            self.abort_background_color = [1, 0, 0, 1]
        # Else the button is disabled and returns to default gray
        else:
            self.abort_disabled = True
            self.abort_background_color = [1, 1, 1, 1]


    def toggle_cmd_status(self):
        """
        Enable/Disable cmd_group buttons:

            * Shutdown
            * Restart
            * Suspend
            * Log Off
        """
        # If the Start/Pause button is down (countdown is active), then
        if self.ids.start_pause.state == 'down':
            # Then preset cmd buttons are down. To apply a preset, Pause or
            # Abort the countdown.
            self.preset_status = True
        # Otherwise they are available and can be selected at any time
        else:
            self.preset_status = False
        self.shutdown_btn_disabled = self.preset_status
        self.restart_btn_disabled = self.preset_status
        self.suspend_btn_disabled = self.preset_status
        self.logoff_btn_disabled = self.preset_status


    def toggle_preset_status(self):
        """
        Enable/Disable preset_duration (time) buttons:
            * 20
            * 40
            * 60
            * 90
            * 120
        """
        # If the Start/Pause button is down (countdown is active), then
        if self.ids.start_pause.state == 'down':
            # Then preset time buttons are down. To apply a preset, Pause or
            # Abort the countdown.
            self.preset_status = True
        # Otherwise they are available and can be selected at any time
        else:
            self.preset_status = False
        self.set20_disabled = self.preset_status
        self.set40_disabled = self.preset_status
        self.set60_disabled = self.preset_status
        self.set90_disabled = self.preset_status
        self.set120_disabled = self.preset_status


    def toggle_start_pause_state(self):
        """
        Toggle the 'Start/Pause' button's state (i.e., up or down).

        When "up", the button is not pressed and the button's text
        says, "Start".

        When "down", the button is pressed and the button's text
        says, "Pause".
        """
        # If Start/Pause says 'Start', then
        if self.start_pause == 'Start':
            # Set the button to 'up'
            self.ids.start_pause.state = 'normal'
        # Else the button is down
        else:
            self.ids.start_pause.state = 'down'


    def reset_preset_state(self):
        """
        Return the preset_duration (time) buttons to the normal (up) state.
        """
        # If countdown is at 0, the presets are in the 'up' state
        if self.countdown == 0:
            self.ids.set20.state = 'normal'
            self.ids.set40.state = 'normal'
            self.ids.set60.state = 'normal'
            self.ids.set90.state = 'normal'
            self.ids.set120.state = 'normal'


    def reset_cmd_state(self):
        """
        Return the cmd_group buttons to the normal (up) state.
        """
        self.ids.shutdown.state = 'normal'
        self.ids.restart.state = 'normal'
        self.ids.suspend.state = 'normal'
        self.ids.logoff.state = 'normal'


    def toggle_start_pause_text(self):
        """
        Toggle the 'Start/Pause' button text label between "Start" and "Pause"
        """
        # If the Start/Pause button is down and the countdown is above 0, then
        if self.ids.start_pause.state == 'down' and self.countdown > 0:
            # The countdown is active, so set the button text to 'Pause'
            self.start_pause = 'Pause'
        # Else, set the text to 'Start'
        else:
            self.start_pause = 'Start'


    def start_stop_timer(self):
        """
        Toggle start/stop the countdown timer.

        By default, cancel any active animation (countdown). If countdown
        time remains on the clock, start the animation (countdown).
        """
        # Cancel any current animation in progress
        Animation.cancel_all(self)
        # Define the rules for Animation; i.e., (where we are going, where
        # we're coming from)
        self.anim = Animation(
            countdown=0,
            duration=self.countdown,
        )
        # on_release of Start/Pause button, if it's down and there is still
        # time on the clock, then
        if self.ids.start_pause.state == 'down' and self.countdown > 0:
            # Get current cmd value
            self.get_cmd()
            # On completion of the countdown, call method to initiate the
            # shutdown process
            self.anim.bind(on_complete=self.initiate_shutdown)
            # Start the animation
            self.anim.start(self)


    def add_time(self, button_time):
        """
        Add time (15 min) to the current countdown (as opposed to
        resetting the clock).
        """
        # The timer must be stopped in order to add time
        self.start_stop_timer()
        # Add to the current countdown time the time of the button that
        # initiated the call
        self.countdown += button_time
        # The timer is then restarted again
        self.start_stop_timer()


    def sub_time(self, button_time):
        """
        Subtract time (15 min) from the current countdown (as opposed
        to resetting the clock).
        """
        # If subtracting time would set the countdown to 0 or less, then
        if button_time >= self.countdown:
            # If the Start/Pause button is 'down', then
            if self.ids.start_pause.state == 'down':
                # Instantiate ImminentPopup
                self.imminent_popup = ImminentPopup(self.cmd)
                # Toggle '+ 15 min' button status
                self.toggle_add_time_status()
                # Disable '- 15 min button'
                self.sub_time_disabled = True
                # Stop the countdown, then
                Animation.cancel_all(self)
                # Call the pop-up to notify User of imminent shutdown,
                # restart, etc.
                self.imminent_popup.open()
                self.popup_active = True
            # Else, Start/Pause is 'normal' and the countdown isn't active, so
            else:
                # Set the countdown to 0
                self.countdown = 0
                # Disable '- 15 min' button
                self.sub_time_disabled = True
        # Else, the timer will remain above 0, so
        else:
            # The timer must be stopped in order to add time, then
            self.start_stop_timer()
            # Subtract from the current countdown time the time of the button
            # that initiated the call
            self.countdown -= button_time
            # The timer is then restarted again
            self.start_stop_timer()


    def popup_yes(self):
        """
        Initiate cmd execution upon 'Yes' response to Final Popup.
        """
        self.countdown = 0
        self.initiate_shutdown()
        self.popup_active = False


    def popup_no(self):
        """
        Dismiss Final Popup and restart the countdown where it left off.
        """
        self.anim.start(self)
        self.toggle_add_time_status()
        self.sub_time_disabled = False
        self.popup_active = False


    def reset(self):
        """
        Reset the App back to default settings.
        """
        Animation.cancel_all(self),
        self.clear_timer(),
        self.toggle_start_pause_status(),
        self.toggle_start_pause_text(),
        self.toggle_start_pause_state(),
        self.toggle_preset_status(),
        self.toggle_cmd_status(),
        self.toggle_sub_time_status(),
        self.toggle_abort_status(),
        self.toggle_keybinding_allowed(),
        self.apply_defaults()


class LinShutdownApp(App):
    """
    Instantiate the root class and apply default settings
    from user_settings_file.
    """
    def build(self):
        shutdown_timer = LinShutdownTimer()
        # shutdown_timer.systray.main()
        shutdown_timer.apply_defaults()
        return shutdown_timer


#Instantiate top-level/root widget and run it.
if __name__ == "__main__":
    LinShutdownApp().run()
