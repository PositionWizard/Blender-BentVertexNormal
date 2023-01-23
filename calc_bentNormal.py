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
    "version": (1, 0, 0),
    "blender": (3, 4, 0),
    "location": "View3D > Mesh > Normals",
    # "warning": "This addon is still in development.",
    "category": "Mesh"
    }
    
import bpy
from mathutils import Vector, Matrix
import math, random

from bpy.props import (
        BoolProperty,
        FloatProperty,
        IntProperty,
        )

# paper on sampling: https://github.com/Bindless-Chicken/Sampling-Python
# code reference: https://blog.thomaspoulet.fr/uniform-sampling-on-unit-hemisphere/
def random_uniform_cosine(u, v):
    sintheta = math.sqrt(-u*(u-2))
    phi = 2 * math.pi * v

    # Switch to cartesian coordinates
    x = sintheta * math.cos(phi)
    y = sintheta * math.sin(phi)

    return x, y

def make_orthonormals(N):
    if(N[0] != N[1] or N[0] != N[2]):
        a = Vector((1, 1, 1)).cross(N)
    else:
        a = Vector((-1, 1, 1)).cross(N)

    a = a.normalized()
    b = N.cross(a)

    return a, b

def sample_cos_hemisphere(N, randu, randv):
    costheta = 1 - randu
    T, B = make_orthonormals(N)
    randu, randv = random_uniform_cosine(randu, randv)

    return (randu * T) + (randv * B) + (costheta * N)


class BENTNORMAL_OT_calculate_normals(bpy.types.Operator):
    bl_idname = "bentnormal.calculate_new_normals"
    bl_label = "Calculate Bent Normal"
    bl_description = "Bend normals of selected vertices to a direction of their least occlusion"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    def upd_min(self, context):
        if self.MaxRayDistance <= self.MinRayDistance:
            if self.MaxRayDistance != 0:
                self.MaxRayDistance = self.MinRayDistance + 0.01

    def upd_max(self, context):
        if self.MinRayDistance >= self.MaxRayDistance:
            if self.MaxRayDistance != 0:
                self.MinRayDistance = self.MaxRayDistance - 0.01

    Samples: IntProperty(
        name="Sample Count",
        description="Number of random rays to test against for calculations.\n"
                    "Higher numbers yield more accurate results",
        default=1024,
        max=131072,
        min=1,
        soft_max=8192,
        soft_min=128,
        )

    MaxRayDistance: FloatProperty(
        name="Max Distance",
        description="Maximuim distance of rays cast from selected vertex.\n"
                    "0 = infinite",
        default=0,
        min=0,
        subtype='DISTANCE',
        unit='LENGTH',
        update=upd_max
        )

    MinRayDistance: FloatProperty(
        name="Min Distance",
        description="Minimum distance of rays cast from selected vertex.\n"
                    "Used to avoid rays hitting at the very point they were cast from",
        default=0.02,
        min=0.001,
        subtype='DISTANCE',
        unit='LENGTH',
        update=upd_min
        )

    NewNormalStrength: FloatProperty(
        name="New Normal Strength",
        description="The strength of bent normal applied to vertices.\n"
                    "0% - Original\n"
                    "100% - Full bent",
        default=100.0,
        min=0.0,
        max=100.0,
        subtype='PERCENTAGE',
        )

    Evaluate_Self_Only: BoolProperty(
        name="Self Only",
        description="Should the rays react only to the active object or an entire scene",
        default=True
        )

    IgnoreBackface: BoolProperty(
        name="Ignore Backfaces",
        description="Should the rays ignore backfaces when calculating the normal",
        default=True
        )

    SamplingSeed: FloatProperty(
        name="Sampling Seed",
        description="Optionally set a different seed for randomness of sampling.\n\n"
                    "Setting this to 0 produces random results everytime.\n"
                    "Anything different will produce consistent results for each calculation",
        default=512
        )

    @classmethod
    def poll(cls, context):
        try: 
            return context.active_object.type == 'MESH'
        except: 
            return False

    def ray_loop(self, sc, obj, base_pos, dir, maxDist, depsgraph, raycast_hit=False, normal=Vector((0,0,0)), hit_pos=Vector((0,0,0))):
        # choose whether to test rays against entire scene or only active object
        if self.Evaluate_Self_Only:
            raycast_hit, hit_pos, normal = obj.ray_cast(base_pos, dir, distance=maxDist, depsgraph=depsgraph)[0:3]
        else:
            raycast_hit, hit_pos, normal = sc.ray_cast(depsgraph, base_pos, dir, distance=maxDist)[0:3]

        # for Ignore Backface option: check if the ray hit a backface, otherwise just stop looking for a frontface
        if self.IgnoreBackface and raycast_hit and normal.dot(dir)>=0 and normal != 0:

            # shorten the max distance by length of a ray so it's always as long as base input
            rayLength_atHit = math.dist(base_pos, hit_pos)
            maxDist = maxDist-rayLength_atHit

            # offset the position of the new ray by the direction
            newRay_pos = hit_pos + (dir/1000)

            self.ray_loop(sc, obj, newRay_pos, dir, maxDist, depsgraph)
        else:
            return raycast_hit


    def execute(self, context):
        sc = context.scene
        obj = context.active_object
        mesh = bpy.types.Mesh(obj.data)
        # depsgraph = bpy.context.evaluated_depsgraph_get()
        depsgraph = context.view_layer.depsgraph
        # ensure that custom normals are enabled and they don't break the mesh
        if not mesh.has_custom_normals:
            mesh.auto_smooth_angle = 180
        mesh.use_auto_smooth = True
        
        
        # change randmness of calculations
        if self.SamplingSeed:
            random.seed(self.SamplingSeed)

        if self.MaxRayDistance == 0.0:
            maxDist = float("inf")
        else:
            maxDist = self.MaxRayDistance-self.MinRayDistance

        # normalize lerp value
        Normal_Lerp = self.NewNormalStrength/100

        # switch modes because we can't read vertex colors in edit mode
        prev_mode = context.object.mode
        bpy.ops.object.mode_set(mode='OBJECT')

        verts_loops = []
        for v in mesh.vertices:
            v = bpy.types.MeshVertex(v)
            if v.select == True:
                # get a list of split-normals as vectors and IDs
                verts_loops.append([v, [i for i in mesh.loops if i.vertex_index == v.index]])

        # prepare a list of unique split-normals as vectors and IDs, which will be calculated later
        mesh.calc_normals_split()
        bake_verts = []
        duped_normals = set()
        for group in verts_loops:
            v = group[0] # vertex
        
            Normal = v.normal
            normal_long = Vector(Normal).copy()

            # inflate cage mesh by averaged normal (always do that)
            if self.MinRayDistance < 0:
                normal_long.negate()
            normal_long.length = abs(self.MinRayDistance)
            vert_farPos = v.co + normal_long

            # loop through split verts
            for i, l in enumerate(group[1]):
                l = bpy.types.MeshLoop(l)
                
                # look for the same vertex normals on the vert and cast them out from sampling (loop through self but only from the current moment)
                for x in group[1][i:]:
                    if x.index != l.index and x.normal == l.normal:
                        duped_normals.add(x)

                # skip preparing a split vert if it's in the duped
                if l not in duped_normals:
                    bake_verts.append([l, vert_farPos])

        # get a list of original split normals
        normals_new = [Vector(l.normal).freeze() for l in mesh.loops]

        for l, pos in bake_verts:
            l = bpy.types.MeshLoop(l)
            Normal = l.normal
            rayNormal = l.normal.copy()

            # get vert position and normal rotation in world space for scene raycasting
            if not self.Evaluate_Self_Only:
                vert_worldMat = obj.matrix_world @ Matrix.Translation(pos)  
                pos = vert_worldMat.translation
                rayNormal.rotate(obj.matrix_world)

            # Do the shader code thingy
            hits = 0
            accumulatedNonOccludedNormals = Vector((0, 0, 0))
            i=0
            while i < self.Samples:
                randu = random.uniform(0.0, 1.0)
                randv = random.uniform(0.0, 1.0)

                ray_R = sample_cos_hemisphere(rayNormal, randu, randv)

                raycast_hit = self.ray_loop(sc, obj, pos, ray_R, maxDist, depsgraph)
                
                if raycast_hit:
                    hits += 1
                    # print("Hit!")
                else:
                    accumulatedNonOccludedNormals += ray_R
                    # print("Miss, accumulating, the normal...")

                i += 1

            if(self.Samples - hits > 0):
                NonOccludedDirection = accumulatedNonOccludedNormals.normalized()

                # rotate the raycast normal backt o local space
                if not self.Evaluate_Self_Only:
                    NonOccludedDirection.rotate(obj.matrix_world.inverted())

                # lerp the normal between original and new one
                NonOccludedDirection = Normal.lerp(NonOccludedDirection, Normal_Lerp).normalized()
            else:
                NonOccludedDirection = Normal

            # look for split verts with duped normals and give them the same new calculated normal
            for x in duped_normals:
                if l.vertex_index == x.vertex_index and Normal == x.normal:
                    normals_new[x.index] = NonOccludedDirection

            # set the split normal to the new bent normal vector
            normals_new[l.index] = NonOccludedDirection

        mesh.normals_split_custom_set(normals_new)
        # switch to previous mode before running the script
        bpy.ops.object.mode_set(mode=prev_mode)

        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


def menu_func(self, context):
    self.layout.operator_context = 'INVOKE_DEFAULT'
    self.layout.operator(BENTNORMAL_OT_calculate_normals.bl_idname)
    
def register():
    bpy.utils.register_class(BENTNORMAL_OT_calculate_normals)
    bpy.types.VIEW3D_MT_edit_mesh_normals.prepend(menu_func)

def unregister():
    bpy.types.VIEW3D_MT_edit_mesh_normals.remove(menu_func)
    bpy.utils.unregister_class(BENTNORMAL_OT_calculate_normals)

if __name__ == "__main__":
    register()