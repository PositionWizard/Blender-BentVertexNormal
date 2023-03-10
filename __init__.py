# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

bl_info = {
    "name": "Bent Normal - Vertex Normal B(l)ender",
    "description": "Calculate normals with direction of least occlusion for chosen vertices.",
    "author": "Czarpos, simonbroggi, sambler",
    "version": (1, 1, 0),
    "blender": (3, 4, 0),
    "location": "View3D > Mesh > Normals",
    # "warning": "This addon is still in development.",
    "category": "Mesh",
    "doc_url": "https://github.com/PositionWizard/Blender-BentVertexNormal/",
    "tracker_url": "https://github.com/PositionWizard/Blender-BentVertexNormal/issues"
    }

if "bpy" in locals():
    import importlib
    if "calc_bent_normal" in locals():
        importlib.reload(calc_bent_normal)

import bpy
from .calc_bent_normal import BENTNORMAL_OT_calculate_normals

def menu_normals(self, context):
    self.layout.operator_context = 'INVOKE_DEFAULT'
    self.layout.operator(BENTNORMAL_OT_calculate_normals.bl_idname)
    
def register():
    bpy.utils.register_class(BENTNORMAL_OT_calculate_normals)
    bpy.types.VIEW3D_MT_edit_mesh_normals.prepend(menu_normals)

def unregister():
    bpy.types.VIEW3D_MT_edit_mesh_normals.remove(menu_normals)
    bpy.utils.unregister_class(BENTNORMAL_OT_calculate_normals)