#!/usr/bin/python
# -*- coding: UTF-8 -*-

__version__ = "1.0.0"

import pdb
import sys
import traceback

from kivy.animation import Animation
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.effects.scroll import ScrollEffect
from kivy.graphics.context_instructions import PopMatrix, PushMatrix, Rotate
from kivy.graphics.instructions import *
from kivy.lang import Builder
from kivy.factory import Factory
from kivy.metrics import dp, sp
from kivy.properties import *
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scatter import Scatter
from kivy.uix.scrollview import ScrollView
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget

from pkg_resources import resource_filename
#KV Files
path = resource_filename( __name__, 'scroll.kv' )
Builder.load_file( path )


class _RefreshScrollEffect( ScrollEffect ) :
    '''
    This class is simply based on DampedScrollEffect.
    If you need any documentation please look at kivy.effects.dampedscrolleffect.
    '''

    edge_damping    = NumericProperty(0.25)
    spring_constant = NumericProperty(2.0)
    min_overscroll  = NumericProperty(.5)
    round_value     = BooleanProperty(True)

    def update_velocity(self, dt):
        if abs(self.velocity) <= self.min_velocity and self.overscroll == 0:
            self.velocity = 0
            # why does this need to be rounded? For now refactored it.
            if self.round_value:
                self.value = round(self.value)
            return

        total_force = self.velocity * self.friction
        if abs(self.overscroll) > self.min_overscroll:
            total_force += self.velocity * self.edge_damping
            total_force += self.overscroll * self.spring_constant
        else:
            self.overscroll = 0

        stop_overscroll = ''
        if not self.is_manual:
            if self.overscroll > 0 and self.velocity < 0:
                stop_overscroll = 'max'
            elif self.overscroll < 0 and self.velocity > 0:
                stop_overscroll = 'min'

        self.velocity = self.velocity - total_force
        if not self.is_manual:
            self.apply_distance(self.velocity * dt)
            if stop_overscroll == 'min' and self.value > self.min:
                self.value = self.min
                self.velocity = 0
                return
            if stop_overscroll == 'max' and self.value < self.max:
                self.value = self.max
                self.velocity = 0
                return
        self.trigger_velocity_update()

    def on_value(self, *args):
        scroll_min = self.min
        scroll_max = self.max
        if scroll_min > scroll_max:
            scroll_min, scroll_max = scroll_max, scroll_min
        if self.value < scroll_min:
            self.overscroll = self.value - scroll_min
        elif self.value > scroll_max:
            self.overscroll = self.value - scroll_max
        else:
            self.overscroll = 0
        self.scroll = self.value

    def on_overscroll(self, *args):
        scroll_view = self.target_widget.parent
        scroll_view._did_overscroll = True
        self.trigger_velocity_update()

    def apply_distance(self, distance):
        os = abs(self.overscroll)
        if os:
            distance /= 1. + os / sp(200.)
        super(_RefreshScrollEffect, self).apply_distance(distance)


class RefreshableScrollView( ScrollView ) :
    '''
    This is a very simple subclass of ScrollView.
    When the user does overscroll the view, a 'ReloadSpinner' is shown.
    You will need to call 'reload_done' once you've dove your loading.
    '''

    on_start_reload = ObjectProperty( None )
    '''
    Will be called whenever overscroll occurs.
    '''

    reload_spinner = ObjectProperty( None )
    root_layout = ObjectProperty( None )

    def __init__( self, **kargs ) :
        super( RefreshableScrollView, self ).__init__( **kargs )
        self.effect_cls = _RefreshScrollEffect
        self._reloading = False
        self._did_overscroll = False

    def on_touch_up( self, *args ) :
        if self._did_overscroll and not self._reloading :
            if self.on_start_reload : self.on_start_reload()
            self.reload_spinner = ReloadSpinner( root_layout=self.root_layout )
            self.reload_spinner.start()     
            self._reloading = True
            self._did_overscroll = False
        return super( RefreshableScrollView, self ).on_touch_up( *args )

    def reload_done( self, *args ) :        
        self._reloading = False
        if self.reload_spinner : self.reload_spinner.stop()
    

class ReloadSpinner( Widget ) :

    root_layout = ObjectProperty( None )
    diameter = NumericProperty( dp(48) )
    font_size = NumericProperty( dp(36) )
    _angle = NumericProperty( 0 )
    _color = ListProperty( [0,0,0,1] )
    duracy = NumericProperty( .2 )

    def __init__( self, **kargs ) :
        super( ReloadSpinner, self ).__init__( **kargs )
    
    def update_animation( self, *args ) :
        self._angle -= 5
    
    def start( self ) :

        self.pos = ( 
            self.root_layout.width/2 - self.width/2, 
            self.root_layout.height+self.height
        )

        animation = Animation( 
            y=self.root_layout.height-2*self.height, 
            duration=self.duracy*1.5
        )
        animation.start( self )         

        self._angle = 0
        self._hex = 0
        self._color = 0, 0, 0, 1 
        self.root_layout.add_widget( self )
        Clock.schedule_interval( self.update_animation, 0.04 )
    
    def stop( self ) : 
        animation = Animation( 
            y=self.root_layout.height-2*self.height, 
            duration=self.duracy
        )
        animation.bind(
            on_complete=self._remove_animation_done
        )
        animation.start( self )         

    def _remove_animation_done( self, *args ) :
        self.root_layout.remove_widget( self )
        Clock.unschedule( self.update_animation )


















