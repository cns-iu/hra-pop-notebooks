#import modules
import bpy
import bmesh
import pandas as pd
import os

def calculate_mesh_volume(mesh):
    """A function to get the volume of a 3D mesh

    Args:
        mesh (mesh): A mesh
    Returns:
        volume (float): the volume in cubic meters
    """
    bm = bmesh.new()
    bm.from_mesh(mesh)
    
    # Ensure lookup tables are generated
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    
    volume = bm.calc_volume(signed=True)
    bm.free()
    return volume


def get_origin(mesh):
    """ A function to get the origin of a mesh
    
    Args:
        mesh (mesh): A mesh
    Returns:
        3D coordinates (tuple): XYZ coordinates
    """

def set_working_directory():
    """Sets the working directory to the same one as the BLEND file
    """ # Get the path of the current blend file
    blend_file_path = bpy.data.filepath

    # Extract the directory from the blend file path
    blend_file_directory = os.path.dirname(blend_file_path)

    # Change the current working directory to the blend file directory
    os.chdir(blend_file_directory)

    # Print to verify the working directory has changed
    print("Current working directory set to:", os.getcwd())

def export_to_csv(df):
    """Write a DataFramer to CSV
    """
    # Write the DataFrame to a CSV file
    print(os.getcwd())
    df.to_csv('output/corridor_volumes.csv', index=False)  # index=False prevents writing row numbers to the CSV
    print("CSV file has been written successfully.")

def main():    
    """The main function to get volume and 3D coordinates for all meshes in the scene, then exporting it to CSV
    """
    
    # set the working directory to the one for the current BLEND file
    set_working_directory()
    
    # create dict for exporting results
    result = {'corridor_number': [], 'volume': []}
    
    # Get the active object
    for obj in bpy.context.selected_objects:
        print(obj.name)
        # Ensure the object is a mesh
        if obj and obj.type == 'MESH':
            volume = calculate_mesh_volume(obj.data)
            result['corridor_number'].append(obj.name)
            result['volume'].append(volume)
            print(f"The volume of the mesh is: {volume}")
        else:
            print("Selected object is not a mesh or no object is selected")
            
    # Convert the dictionary to a DataFrame
    df = pd.DataFrame(result)
    
    export_to_csv(df)

if __name__ == "__main__":
    main()


