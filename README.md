# About
### Normal calculator allowing to bend vertex normals in the direction of its least occlusion.

A single operator named **Calculate Bent Normal**, available only in edit mode under **Mesh -> Normals (Altr+N)** panel. Calculates new vertex normals for selected vertices, bending the normals to a new direction in which most ambient light is coming from.

The operator is based on raycasting and randomness so that results may not always be perfectly accurate. The accuraccy depends on sample conut but it's good to keep in mind that higher sampling will take longer and ***doing this for large number of vertices can freeze Blender for a while.***

![Demo](https://user-images.githubusercontent.com/89351809/214152754-6a704bb1-2f0a-4c19-acc6-78e681f2e57b.gif)

# Usage
Go into Edit Mode, select vertices you want to calculate for and run the operator.
The tool has a few options you can tweak to get different results:

![Operator options](https://user-images.githubusercontent.com/89351809/214150472-31308fac-2aac-478d-ad7d-36b6fac6f991.png)

- **Operator Presets**: You can define custom parameters then save a preset for convenience
- **Sample Count**: Number of random rays to test against for calculations.
  - Higher numbers yield more accurate results.
  - For most optimal results, set this to around 2-4k
- **Max Distance**: Maximuim distance of rays cast from selected vertex.
  - Setting this to 0, makes max rays infinite long.
- **Min Distance**: Minimum distance of rays cast from selected vertex. Used to avoid rays hitting at the very point they were cast from.
  - Cannot be longer than Max Distance.
- **New Normal Strength**: The strength of bent normal applied to vertices, expressed in percentage.
  - 0% - Original normal
  - 100% - Full bent
- **Self Only**: Whether the rays should be tested only against the active object or an entire scene.
  - Enabled - Rays ignore anything outside the active object.
  - Disabled - Rays react to everything visible in the scene.
- **Ignore Backfaces**: Should the rays ignore backfaces when calculating the normal.
- **SamplingSeed**: Optional parameter setting a different seed for randomness of sampling.
  - Setting this 0, produces random results everytime the operator is ran
  - Anything different will produce consistent calculations everytime (recommended to work with)
