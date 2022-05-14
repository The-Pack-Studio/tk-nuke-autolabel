# Copyright (c) 2013 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

'''
to-do=:
Change the color of the read node to red if there's a newer version of the pass. Might be overkill ?
'''


import os
import nuke
import tank
from tank import TankError


class NukeAutolabel(tank.platform.Application):

    def init_app(self):
        """
        Called as the application is being initialized
        """

        # this app should not do anything if nuke is run without gui.

        if nuke.env['gui']:

            self.log_debug("Loading tk-nuke-autolabel app.")
            self._add_callbacks()

            self.beauty_tile_color = self.tileColorConvert(self.get_setting('beauty_tile_color'))
            self.other3d_tile_color = self.tileColorConvert(self.get_setting('other3d_tile_color'))


        else:
            pass


    def destroy_app(self):
        """
        Called when the app is unloaded/destroyed
        """
        self.log_debug("Destroying tk-nuke-autolabel app")
        
        # remove any callbacks that were registered by the handler:
        self._remove_callbacks()        


    def _add_callbacks(self):
        """
        Add callbacks to watch for certain events:
        """
        nuke.addAutolabel(self.setReadLabel, nodeClass='Read')
        nuke.addAutolabel(self.setReadLabel, nodeClass='DeepRead')

    def _remove_callbacks(self):
        """
        Removed previously added callbacks
        """
        nuke.removeAutolabel(self.setReadLabel, nodeClass='Read')
        nuke.removeAutolabel(self.setReadLabel, nodeClass='DeepRead')


    def tileColorConvert(self, tile_color):
        """
        converts from color triplet (r,g,b, 0 to 255 to packed rgb used for nuke's tile_color knob)
        code borrowed from tk-nuke-writenode
        """
        
        packed_rgb = 0
        for element in tile_color:
            packed_rgb = (packed_rgb + min(max(element, 0), 255)) << 8 
        return packed_rgb



    def setReadLabel(self):


        tk = self.sgtk
        context = self.context

        readNode = nuke.thisNode()
        name = readNode.name()
        currentFrame = readNode.knob('file').evaluate()
        currentFrame = os.path.basename(currentFrame)
        userlabel = readNode.knob('label').value()
        colorspace = ""
        if not "DeepRead" in readNode.Class(): # DeepRead nodes have no colorspace knob
            colorspace = readNode.knob("colorspace").value()
            colorspace = "({})".format(colorspace)

        labelStart = "{}\n{}".format(name, currentFrame)
        imagePath = readNode.knob('file').toScript()
        imagePath = nuke.filenameFilter(imagePath)

        labelMiddle = ''
        RenderLayer = ''
        Camera = ''
        AOV = ''

        tmpl = tk.template_from_path(imagePath)
        if tmpl:
            if tmpl.name in self.get_setting('render3d_templates'): # if the template corresponds to one from the list defined in the app settings

                fields = tmpl.get_fields(imagePath)

                if fields.get("RenderLayer"):
                    RenderLayer = str(fields.get("RenderLayer"))
                if fields.get("Camera"):
                    Camera = str(fields.get("Camera"))
                if fields.get("AOV"):
                    AOV = str(fields.get("AOV"))

                if Camera == 'beauty' or AOV == 'beauty' or Camera == 'RGBA' or AOV == 'RGBA': 
                    readNode.knob('tile_color').setValue(self.beauty_tile_color)
                else :
                    readNode.knob('tile_color').setValue(self.other3d_tile_color)

                labelMiddle = ':'.join([x for x in [RenderLayer, Camera, AOV] if x != ''])


            if tmpl.name in self.get_setting('hiero_templates'):

                fields = tmpl.get_fields(imagePath)

                hiero_type_field = self.get_setting('hiero_type_field')
                hiero_type_colors = self.get_setting("hiero_type_colors")

                if fields.get(hiero_type_field): # the field exists, set it in uppercase on the node label
                    labelMiddle = fields.get(hiero_type_field).upper()

                plate_context = tk.context_from_path(imagePath)
                if context.entity and plate_context.entity and context.entity == plate_context.entity: # only apply to renders pertaining to the current context
                    if fields.get(hiero_type_field) in hiero_type_colors:
                        color = hiero_type_colors[fields.get(hiero_type_field)]
                        color = self.tileColorConvert(color)
                        readNode.knob('tile_color').setValue(color)
                    else:
                        color = self.get_setting("hiero_default_color")
                        color = self.tileColorConvert(color)
                        readNode.knob('tile_color').setValue(color)

            full_label = "\n".join([ x for x in [labelStart, labelMiddle, colorspace, userlabel] if x != ''])
            
            return full_label

        else:
            return None                

