```bash
$ PotreeConverter -h                                      
  -i [ --source ]                        input files
  -h [ --help ]                          prints usage
  -p [ --generate-page ]                 Generates a ready to use web page with the given name.
  -o [ --outdir ]                        output directory
  -s [ --spacing ]                       Distance between points at root level. Distance halves each level.
  -d [ --spacing-by-diagonal-fraction ]  Maximum number of points on the diagonal in the first level (sets spacing). spacing = diagonal value
  -l [ --levels ]                        Number of levels that will be generated. 0: only root, 1: root and its children, ...
  -f [ --input-format ]                  Input format. xyz: cartesian coordinates as floats, rgb: colors as numbers, i: intensity as number
  --color-range
  --intensity-range
  --output-format                        Output format can be BINARY, LAS or LAZ. Default is BINARY
  -a [ --output-attributes ]             can be any combination of RGB, INTENSITY and CLASSIFICATION. Default is RGB.
  --scale                                Scale of the X, Y, Z coordinate in LAS and LAZ files.
  --aabb                                 Bounding cube as "minX minY minZ maxX maxY maxZ". If not provided it is automatically computed
  --incremental                          Add new points to existing conversion
  --overwrite                            Replace existing conversion at target directory
  --source-listing-only                  Create a sources.json but no octree.
  --projection                           Specify projection in proj4 format.
  --list-of-files                        A text file containing a list of files to be converted.
  --source                               Source file. Can be LAS, LAZ, PTX or PLY
  --title                                Page title
  --description                          Description to be shown in the page.
  --edl-enabled                          Enable Eye-Dome-Lighting.
  --show-skybox
  --material                             RGB, ELEVATION, INTENSITY, INTENSITY_GRADIENT, RETURN_NUMBER, SOURCE, LEVEL_OF_DETAIL
```