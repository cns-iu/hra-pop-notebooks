import pandas as pd
import os
import subprocess

off_dir = './plain_off'
output_dir = './intersection_volume/'
os.makedirs(output_dir, exist_ok=True)

df = pd.read_csv('./mesh-pair-intersection-extraction-sites.csv')

for index, row in df.iterrows():
    organ = row['organ']
    source = row['source']
    target = row['target']
    sum_extraction_sites_number = row['sum_extraction_sites_number']
    
    if sum_extraction_sites_number > 0:
        mesh1 = os.path.join(off_dir, organ, source + '.off')
        mesh2 = os.path.join(off_dir, organ, target + '.off')
        print(mesh1)
        print(mesh2)
        output_filename = source + "-" + target + "-intersection-volume.off"
        output_path = os.path.join(output_dir, output_filename)
        command = ['./exact_intersection_space/build/compute_intersection_space', mesh1, mesh2, output_path]
        subprocess.run(command)
    